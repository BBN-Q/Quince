# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the windows, view, and scene descriptions

# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
# from PyQt5.QtSvg import *
# from PyQt5.QtWidgets import *

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtSvg import *
from qtpy.QtWidgets import *

from functools import partial
from JSONLibraryUtils.FileWatcher import LibraryFileWatcher
import json
import glob
import time
import os.path
import numpy as np

from .node import *
from .wire import *
from .param import *
from .graph import *
from .util import *
from .inspect import *

def strip_vendor_names(instr_name):
    vns = ["Agilent", "Alazar", "Keysight", "Holzworth", "Yoko", "Yokogawa"]
    for vn in vns:
        instr_name = instr_name.replace(vn, "")
    return instr_name

def correct_resource_name(resource_name):
    substs = {"USB::": "USB0::", }
    for k, v in substs.items():
        resource_name = resource_name.replace(k, v)
    return resource_name

class NodeScene(QGraphicsScene):
    """docstring for NodeScene"""
    def __init__(self, window=None):
        super(NodeScene, self).__init__()
        self.window = window
        self.backdrop = QGraphicsRectItem()
        self.backdrop.setRect(-10000,-10000,20000,20000)
        self.backdrop.setZValue(-100)
        self.setBackgroundBrush(QBrush(QColor(60,60,60)))

        self.addItem(self.backdrop)
        self.view = None

        self.menu = QMenu()
        self.sub_menus = {}
        self.generate_menus()

        self.menu.addSeparator()
        clear_wires = QAction('Clear Wires', self)
        clear_wires.triggered.connect(self.clear_wires)
        self.menu.addAction(clear_wires)

        self.last_click = self.backdrop.pos()

        self.settings = QSettings("BBN", "Quince")

        self.undo_stack = QUndoStack(self)

    def connectors_nearby(self, position, exclude=[]):
        connectors = [i for i in self.items() if isinstance(i, Connector)
                                              and i.connector_type == 'input'
                                              and i not in exclude]
        rs = {}
        for i, conn in enumerate(connectors):
            p = (position - conn.scenePos())
            r = np.sqrt(p.x()*p.x() + p.y()*p.y())
            if r < 30.0:
                rs[conn] = r
                scale = 1.0+3.0/(r+0.2)
                if scale > 1.5:
                    scale = 1.5
                conn.setRect(-5.0*scale, -5.0*scale, 10*scale, 10*scale)
            else:
                conn.setRect(-5.0, -5.0, 10, 10)
        if len(rs) > 0:
            return sorted(rs, key=rs.get)[0]
        else:
            return None

    def mouseMoveEvent(self, event):
        self.crowded_connectors_nearby(event.scenePos())
        return super(NodeScene, self).mouseMoveEvent(event)

    def crowded_connectors_nearby(self, position):
        conns = [i for i in self.items() if isinstance(i, Connector)]
        for conn in conns:
            if conn.connector_type == 'input' and len(conn.wires_in) > 1:
                p = (position - conn.scenePos())
                r = np.sqrt(p.x()*p.x() + p.y()*p.y())
                if r < 30.0:
                    conn.explode_wires()
                else:
                    conn.implode_wires()

    def clear_wires(self, only_clear_orphaned=False):
        wires = [i for i in self.items() if isinstance(i, Wire)]
        for wire in wires:
            if only_clear_orphaned:
                if wire.end_obj is None:
                    self.removeItem(wire)
                elif wire.start_obj is None:
                    self.removeItem(wire)
            else:
                self.removeItem(wire)

    def open_add_menu(self, location):
        self.menu.exec_(location)

    def contextMenuEvent(self, event):
        self.last_click = event.scenePos()
        self.open_add_menu(event.screenPos())

    def generate_menus(self):
        def parse_node_file(filename):
            with open(filename) as data_file:
                cat  = os.path.basename(os.path.dirname(filename))
                data = json.load(data_file)

                # Create a QAction and add to the menu
                action = QAction(data['name'], self)

                # Create function for dropping node on canvas
                def create(the_data, cat_name):
                    node = Node(the_data['name'])
                    node.cat_name = cat_name
                    for op in the_data['outputs']:
                        node.add_output(Connector(op, 'output'))
                    for ip in the_data['inputs']:
                        node.add_input(Connector(ip, 'input'))
                    for p in the_data['parameters']:
                        if p['type'] == 'str':
                            pp = StringParameter(p['name'])
                        elif p['type'] == 'filename':
                            pp = FilenameParameter(p['name'])
                        elif p['type'] == 'float':
                            pp = NumericalParameter(p['name'], float, p['low'], p['high'], p['increment'], p['snap'])
                        elif p['type'] == 'int':
                            pp = NumericalParameter(p['name'], int, p['low'], p['high'], p['increment'], p['snap'])
                        elif p['type'] == 'combo':
                            pp = ComboParameter(p['name'], p['choices'])
                        elif p['type'] == 'boolean':
                            pp = BooleanParameter(p['name'])

                        if 'default' in p.keys():
                            pp.set_value(p['default'])

                        pp.has_input = False

                        # # Generally, combo, bool, file parameters have no input connectors
                        # if p['type'] in ['combo', 'boolean', 'filename']:
                        #     pp.has_input = False

                        # # If the has_input value is set in the json, pay attention
                        # if 'has_input' in p.keys():
                        #     pp.has_input = p['has_input']

                        # Special parameters cannot be directly edited
                        if 'interactive' in p.keys():
                            pp.set_interactive(p['interactive'])

                        node.add_parameter(pp)

                    # Connector constraints
                    if 'allowed_destinations' in the_data.keys():
                        node.allowed_destinations = the_data['allowed_destinations']

                    # Set the class and module infor for PyQLab
                    node.x__class__  = the_data['x__class__']
                    node.x__module__ = the_data['x__module__']

                    # Custom coloring
                    if cat_name == "Inputs":
                        node.set_title_color(QColor(80,100,70))
                    elif cat_name == "Outputs":
                        node.set_title_color(QColor(120,70,70))
                    # See if names will be duplicated
                    node_names = [i.label.toPlainText() for i in self.items() if isinstance(i, Node)]
                    nan = next_available_name(node_names, the_data['name'])
                    node.label.setPlainText(nan)

                    node.setPos(self.backdrop.mapFromParent(self.last_click))
                    node.setPos(self.last_click)
                    self.addItem(node)
                    return node

                # Add to class
                name = "create_"+("".join(data['name'].split()))
                setattr(self, name, partial(create, data, cat))
                func = getattr(self, name)

                # Connect trigger for action
                create_command = lambda: self.undo_stack.push(CommandAddNode(name, func, self))
                action.triggered.connect(create_command)
                self.sub_menus[cat].addAction(action)

        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "auspex-nodes")
        node_files = sorted(glob.glob(path+'/*/*.json'))
        categories = set([os.path.basename(os.path.dirname(nf)) for nf in node_files])

        for cat in sorted(categories, key=lambda s: s.lower()):
            sm = self.menu.addMenu(cat)
            self.sub_menus[cat] = sm

        for nf in node_files:
            parse_node_file(nf)

        # Now add the instruments
        self.menu.addSeparator()
        self.instruments_menu = self.menu.addMenu("instruments")
        self.sub_menus["instruments"] = self.instruments_menu

        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "auspex-nodes/instruments")
        node_files = sorted(glob.glob(path+'/*/*.json'))
        categories = set([os.path.basename(os.path.dirname(nf)) for nf in node_files])

        for cat in sorted(categories, key=lambda s: s.lower()):
            sm = self.instruments_menu.addMenu(cat)
            self.sub_menus[cat] = sm

        for nf in node_files:
            parse_node_file(nf)

    def load_pyqlab(self):

        name_changes = {'KernelIntegration': 'KernelIntegrator',
                        'DigitalDemod': 'Channelizer'}

        with open(self.window.measFile, 'r') as FID:
            settings = json.load(FID)
            self.meas_settings = settings["filterDict"]
            self.meas_settings_version = settings["version"]

        with open(self.window.instrFile, 'r') as FID:
            self.instr_settings = json.load(FID)["instrDict"]

        with open(self.window.sweepFile, 'r') as FID:
            self.sweep_settings = json.load(FID)["sweepDict"]

        self.loaded_measure_nodes = {} # Keep track of nodes we create
        self.loaded_instr_nodes = {} # Keep track of nodes we create

        # Create and place the filters
        for meas_par in self.meas_settings.values():

            meas_name = meas_par["label"]
            meas_type = meas_par["x__class__"]
            # Perform some translation
            if meas_type in name_changes.keys():
                meas_type = name_changes[meas_type]
            # See if the filter exists, and then create it
            if hasattr(self, 'create_'+meas_type):
                new_node = getattr(self, 'create_'+meas_type)()
                new_node.enabled = meas_par['enabled']
                new_node.base_params = meas_par
                new_node.setOpacity(0.0)
                stored_loc = self.settings.value("node_positions/" + meas_name + "_pos")
                if stored_loc is not None and isinstance(stored_loc, QPointF):
                    new_node.setPos(stored_loc)
                else:
                    new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
                new_node.label.setPlainText(meas_name)
                self.loaded_measure_nodes[meas_name] = new_node

        # Create and place the instruments
        for instr_par in self.instr_settings.values():
            instr_name = instr_par["label"]
            instr_type = instr_par["x__class__"]
            # Perform some translation
            if instr_type in name_changes.keys():
                instr_type = name_changes[instr_type]
            # See if the filter exists, and then create it
            if hasattr(self, 'create_'+instr_type):
                new_node = getattr(self, 'create_'+instr_type)()
                new_node.enabled = instr_par['enabled']
                new_node.base_params = instr_par
                new_node.setOpacity(0.0)
                stored_loc = self.settings.value("node_positions/" + instr_name + "_pos")
                if stored_loc is not None:
                    new_node.setPos(stored_loc)
                else:
                    new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
                new_node.label.setPlainText(instr_name)
                self.loaded_instr_nodes[instr_name] = new_node

        for name, node in self.loaded_measure_nodes.items():
            meas_name = self.meas_settings[name]["label"]

            # Get the source name. If it contains a colon, then the part before the colon
            # is the node name and the part after is the connector name. Otherwise, the
            # connector name is just "source" and the source name is the node name.

            source = self.meas_settings[name]["data_source"].split(":")
            node_name = source[0]
            conn_name = "source"
            if len(source) == 2:
                conn_name = source[1]

            if node_name in self.loaded_measure_nodes.keys():
                start_node = self.loaded_measure_nodes[node_name]
                if conn_name in start_node.outputs.keys():
                    if 'sink' in node.inputs.keys():
                        # Create wire and register with scene
                        new_wire = Wire(start_node.outputs[conn_name])
                        new_wire.setOpacity(0.0)
                        self.addItem(new_wire)

                        # Add to start node
                        new_wire.set_start(start_node.outputs[conn_name].scenePos())
                        start_node.outputs[conn_name].wires_out.append(new_wire)

                        # Add to end node
                        new_wire.end_obj = node.inputs['sink']
                        new_wire.set_end(node.inputs['sink'].scenePos())
                        node.inputs['sink'].wires_in.append(new_wire)
                    else:
                        print("Could not find sink connector in", meas_name)
                else:
                    print("Could not find source connector ", conn_name, "for node", node_name)

            elif node_name in self.loaded_instr_nodes.keys():
                start_node = self.loaded_instr_nodes[node_name]
                if conn_name in start_node.outputs.keys():
                    if 'sink' in node.inputs.keys():
                        # Create wire and register with scene
                        new_wire = Wire(start_node.outputs[conn_name])
                        new_wire.setOpacity(0.0)
                        self.addItem(new_wire)

                        # Add to start node
                        new_wire.set_start(start_node.outputs[conn_name].scenePos())
                        start_node.outputs[conn_name].wires_out.append(new_wire)

                        # Add to end node
                        new_wire.end_obj = node.inputs['sink']
                        new_wire.set_end(node.inputs['sink'].scenePos())
                        node.inputs['sink'].wires_in.append(new_wire)
                    else:
                        print("Could not find sink connector ", conn_name)
            else:
                print("Could not find data_source")

            self.fade_in_items()

    def fade_in_items(self):
        self.draw_i = 0
        self.increment = 15
        self.duration = 300

        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.advance)
        self.fade_timer.start(self.increment)

    def advance(self):
        if self.draw_i < self.duration:
            for i in self.items():
                if isinstance(i, Node) or isinstance(i, Wire):
                    i.setOpacity(float(self.draw_i)/self.duration)
            self.draw_i += self.increment
        else:
            for i in self.items():
                if isinstance(i, Node) or isinstance(i, Wire):
                    i.setOpacity(1.0)
            self.fade_timer.stop()

    def reload_pyqlab(self):
        # Don't retain any undo information, since it is outdated
        self.undo_stack.clear()

        # Reconstruct the scene
        nodes = [i for i in self.items() if isinstance(i, Node)]
        wires = [i for i in self.items() if isinstance(i, Wire)]
        for o in nodes+wires:
            self.removeItem(o)
        self.load_pyqlab()

    def save_node_positions_to_settings(self):
        for n in [i for i in self.items() if isinstance(i, Node)]:
            self.settings.setValue("node_positions/" + n.label.toPlainText() + "_pos", n.pos())
        self.settings.sync()

    def save_for_pyqlab(self):
        self.save_node_positions_to_settings()

        if not hasattr(self, 'meas_settings'):
            self.window.set_status("Not launched from PyQLab, and therefore cannot save to PyQLab JSON.")
            return
        with open(self.window.measFile, 'w') as df:
            nodes  = [i for i in self.items() if isinstance(i, Node)]

            data = {}
            data["filterDict"]  = {n.label.toPlainText(): n.dict_repr() for n in nodes if n.x__module__ == 'MeasFilters'}
            data["version"]     = self.meas_settings_version
            data["x__class__"]  = "MeasFilterLibrary"
            data["x__module__"] = "MeasFilters"

            self.window.ignore_file_updates = True
            self.window.ignore_timer.start()
            json.dump(data, df, sort_keys=True, indent=4, separators=(',', ': '))

    def create_node_by_name(self, name):
        create_node_func_name = "create_"+("".join(name.split()))
        if hasattr(self, create_node_func_name):
            new_node = getattr(self, create_node_func_name)()
            return new_node
        else:
            self.window.set_status("Could not create a node of the requested type.")
            return None

    def removeItem(self, item):
        super(NodeScene, self).removeItem(item)

    def addItem(self, item):
        super(NodeScene, self).addItem(item)

class NodeView(QGraphicsView):
    """docstring for NodeView"""
    def __init__(self, scene):
        super(NodeView, self).__init__(scene)
        self.scene = scene
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.current_scale = 1.0

    def wheelEvent(self, event):
        change = 0.001*event.angleDelta().y()/2.0
        self.scale(1+change, 1+change)
        self.current_scale *= 1+change

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            selected_nodes = [i for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
            self.scene.undo_stack.push(CommandDeleteNodes(selected_nodes, self.scene))
        else:
            return super(NodeView, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MidButton) or (event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            return super(NodeView, self).mousePressEvent(fake)
        elif event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        return super(NodeView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MidButton) or (event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier):
            self.setDragMode(QGraphicsView.NoDrag)
            fake = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            return super(NodeView, self).mouseReleaseEvent(fake)
        elif event.button() == Qt.LeftButton:
            a = super(NodeView, self).mouseReleaseEvent(event)
            self.setDragMode(QGraphicsView.NoDrag)
            return a
        return super(NodeView, self).mouseReleaseEvent(event)

class NodeWindow(QMainWindow):
    """docstring for NodeWindow"""
    def __init__(self, parent=None):
        super(NodeWindow, self).__init__(parent=parent)
        self.setWindowTitle("Nodes")
        self.setGeometry(50,50,1300,600)

        # Setup graphics
        self.scene = NodeScene(window=self)
        self.view  = NodeView(self.scene)

        # Setup menu
        self.status_bar = self.statusBar()

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QApplication.instance().quit)

        saveAction = QAction('&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.save)

        selectAllAction = QAction('&Select All', self)
        selectAllAction.setShortcut('Ctrl+A')
        selectAllAction.setStatusTip('Select All')
        selectAllAction.triggered.connect(self.select_all)

        selectAllConnectedAction = QAction('&Select All Connected', self)
        selectAllConnectedAction.setShortcut('Shift+Ctrl+A')
        selectAllConnectedAction.setStatusTip('Select All Connected')
        selectAllConnectedAction.triggered.connect(self.select_all_connected)

        collapseAllAction = QAction('&Collapse All', self)
        collapseAllAction.setShortcut('Ctrl+K')
        collapseAllAction.setStatusTip('Collapse All')
        collapseAllAction.triggered.connect(self.collapse_all)

        toggleEnabledAction = QAction('&Toggle Descendants', self)
        toggleEnabledAction.setShortcut('Ctrl+E')
        toggleEnabledAction.setStatusTip('Toggle the Enabled/Disabled status of all descendant nodes.')
        toggleEnabledAction.triggered.connect(self.toggle_enable_descendants)

        duplicateAction = QAction('&Duplicate', self)
        duplicateAction.setShortcut('Ctrl+D')
        duplicateAction.setStatusTip('Duplicate')
        duplicateAction.triggered.connect(self.duplicate)

        undoAction = QAction('&Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.setStatusTip('Undo')
        undoAction.triggered.connect(self.undo)

        redoAction = QAction('&Redo', self)
        redoAction.setShortcut('Shift+Ctrl+Z')
        redoAction.setStatusTip('Redo')
        redoAction.triggered.connect(self.redo)

        fileMenu = self.menuBar().addMenu('&File')
        editMenu = self.menuBar().addMenu('&Edit')
        helpMenu = self.menuBar().addMenu('&Help')
        # fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        # fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)
        editMenu.addAction(selectAllAction)
        editMenu.addAction(selectAllConnectedAction)
        editMenu.addAction(collapseAllAction)
        editMenu.addAction(toggleEnabledAction)
        editMenu.addAction(duplicateAction)
        editMenu.addSeparator()
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)

        # Setup layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.view)
        self.hbox.setContentsMargins(0,0,0,0)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.hbox)

        self.setCentralWidget(self.main_widget)

        # Create the pipeline start node if possible
        if hasattr(self.scene, 'create_PipelineStart'):
            ps = self.scene.create_PipelineStart()
            ps.setPos(-300,0)

        svg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets/quince.svg")
        svgrend = QSvgRenderer(svg_path)

        self.svgitem = QGraphicsSvgItem()
        self.svgitem.setSharedRenderer(svgrend)
        self.scene.addItem(self.svgitem)
        self.svgitem.setScale(0.5)
        self.svgitem.setPos(self.svgitem.pos().x()-self.svgitem.boundingRect().width()/4,
                            self.svgitem.pos().y()-self.svgitem.boundingRect().height()/4)

        self.svg_animation = QPropertyAnimation(self.svgitem, bytes("opacity".encode("ascii")))
        self.svg_animation.setDuration(2000)
        self.svg_animation.setStartValue(1.0)
        self.svg_animation.setEndValue(0.0)
        self.svg_animation.start()

    def set_status(self, text, time=2000):
        self.status_bar.showMessage(text, time)

    def load_pyqlab(self, measFile=None, sweepFile=None, instrFile=None):
        if None in [measFile, sweepFile, instrFile]:
            self.set_status("Did not receive all relevant files from PyQLab.")
            return

        self.set_status("Loading PyQLab configuration files...")

        self.measFile  = measFile
        self.sweepFile = sweepFile
        self.instrFile = instrFile

        # Delay timer to avoid multiple firings
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_pyqlab)

        # Delay timer to avoid multiple firings
        self.ignore_file_updates = False
        self.ignore_timer = QTimer(self)
        self.ignore_timer.setSingleShot(True)
        self.ignore_timer.setInterval(1500)
        self.ignore_timer.timeout.connect(self.stop_ignoring_updates)

        # Establish File Watchers for these config files:
        self.watcher = QFileSystemWatcher()
        for f in [measFile, sweepFile, instrFile]:
            self.watcher.addPath(f)
        self.watcher.fileChanged.connect(self.pyqlab_needs_update)

        self.update_timer.start()

    def stop_ignoring_updates(self):
        self.ignore_file_updates = False

    def pyqlab_needs_update(self, path):
        if not self.update_timer.isActive() and not self.ignore_file_updates:
            self.update_timer.start()

    def update_pyqlab(self):
        self.set_status("Files changed on disk, reloading.")
        self.scene.reload_pyqlab()

    def save(self):
        self.scene.save_for_pyqlab()

    def undo(self):
        self.scene.undo_stack.undo()

    def redo(self):
        self.scene.undo_stack.redo()

    def select_all(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            n.setSelected(True)

    def select_all_connected(self):
        selected_nodes = [i.label.toPlainText() for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
        wires = [i for i in self.scene.items() if isinstance(i, Wire)]
        nodes_by_label = {i.label.toPlainText(): i for i in self.scene.items() if isinstance(i, Node)}
        graph = generate_graph(wires)

        items = []
        for sn in selected_nodes:
            sub_graph_items = items_on_subgraph(graph, sn)
            items.extend(sub_graph_items)

        for i in items:
            nodes_by_label[i].setSelected(True)

    def toggle_enable_descendants(self):
        selected_nodes = [i.label.toPlainText() for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]

        if len(selected_nodes) == 0:
            self.set_status("No nodes selected.")
            return
        wires = [i for i in self.scene.items() if isinstance(i, Wire)]
        nodes_by_label = {i.label.toPlainText(): i for i in self.scene.items() if isinstance(i, Node)}
        graph = generate_graph(wires, dag=True)

        items = []
        items.extend(selected_nodes)
        for sn in selected_nodes:
            descs = descendants(graph, sn)
            items.extend(descs)

        new_status = not nodes_by_label[selected_nodes[0]].enabled

        for i in items:
            nodes_by_label[i].enabled = new_status

    def collapse_all(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            n.change_collapsed_state(True)

    def duplicate(self):
        selected_nodes = [i for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
        self.scene.undo_stack.push(CommandDuplicateNodes(selected_nodes, self.scene))

    def cleanup(self):
        # Have to manually close proxy widgets
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            for k, v in n.parameters.items():
                pass
