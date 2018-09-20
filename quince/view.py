# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the windows, view, and scene descriptions

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtSvg import *
from qtpy.QtWidgets import *

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
from .load import *

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

        self.qr = QRectF(-10000,-10000,20000,20000)
        self.setSceneRect(self.qr)
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

        self.qt_settings = QSettings("BBN", "Quince")

        self.undo_stack = QUndoStack(self)

        self.update_screen()

    def update_screen(self):
        if hasattr(self.window, 'view'):
            dpr = self.window.devicePixelRatio()
            nodes = [i for i in self.items() if isinstance(i, Node)]
            _ = [n.update_screen(dpr) for n in nodes]

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
        # Parse Auspex directly
        parse_quince_modules(self)

    def load_yaml(self):
        load_from_yaml(self)

    def reload_yaml(self):
        # Store node settings before reloading
        self.save_node_positions_to_settings()

        # Don't retain any undo information, since it is outdated
        self.undo_stack.clear()

        # Reconstruct the scene
        nodes = [i for i in self.items() if isinstance(i, Node)]
        wires = [i for i in self.items() if isinstance(i, Wire)]
        for o in nodes+wires:
            self.removeItem(o)
        self.load_yaml()

    def save_node_positions_to_settings(self):
        for n in [i for i in self.items() if isinstance(i, Node)]:
            self.qt_settings.setValue("node_positions/" + n.label.toPlainText() + "_pos_x", n.pos().x())
            self.qt_settings.setValue("node_positions/" + n.label.toPlainText() + "_pos_y", n.pos().y())
        self.qt_settings.sync()

    def save_for_yaml(self):
        self.save_node_positions_to_settings()

        nodes      = [i for i in self.items() if isinstance(i, Node)]
        node_names = [n.label.toPlainText() for n in nodes]

        if not hasattr(self, 'settings'):
            self.window.set_status("Not launched with yaml config. Cannot save to yaml.")
            return

        # Start from the original config file in order that we can save comments
        # and other human-friendly conveniences.
        for node, node_name in zip(nodes, node_names):
            if node.is_instrument:
                # Create a new entry if necessary
                if node_name not in self.settings["instruments"].keys():
                    self.settings["instruments"][node_name] = {}
                for k, v in node.dict_repr().items():
                    self.settings["instruments"][node_name][k] = v
            else:
                # Create a new entry if necessary
                if node_name not in self.settings["filters"].keys():
                    self.settings["filters"][node_name] = {}
                for k, v in node.dict_repr().items():
                    self.settings["filters"][node_name][k] = v

        # Prune stale (deleted) filters from the config, but
        # leave instruments other than digitizers alone
        for section in ("filters", "instruments"):
            for name in list(self.settings[section].keys()):
                if name not in node_names:
                    if section=="instruments" and "rx_channels" not in self.settings[section][name].keys():
                        continue
                    self.settings[section].pop(name)

        self.window.ignore_file_updates = True
        self.window.ignore_timer.start()
        yaml_dump(self.settings, self.window.meas_file)

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
        self.centerOn(self.scene.qr.center())

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.current_scale = 1.0

    def wheelEvent(self, event):
        change = 0.001*event.angleDelta().y()/2.0
        self.scale(1+change, 1+change)
        self.current_scale *= 1+change

    def keyPressEvent(self, event):
        if not self.scene.focusItem() and event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
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

        constructExperimentAction = QAction('&Construct Experiment', self)
        constructExperimentAction.setShortcut('Shift+Ctrl+E')
        constructExperimentAction.setStatusTip('Construct Experiment')
        constructExperimentAction.triggered.connect(self.construct_experiment)

        collapseAllAction = QAction('&Collapse All', self)
        collapseAllAction.setShortcut('Ctrl+K')
        collapseAllAction.setStatusTip('Collapse All')
        collapseAllAction.triggered.connect(self.collapse_all)

        expandAllAction = QAction('&Expand All', self)
        expandAllAction.setShortcut('Shift+Ctrl+K')
        expandAllAction.setStatusTip('Expand All')
        expandAllAction.triggered.connect(self.expand_all)

        toggleEnabledAction = QAction('&Toggle Descendants', self)
        toggleEnabledAction.setShortcut('Ctrl+E')
        toggleEnabledAction.setStatusTip('Toggle the Enabled/Disabled status of all descendant nodes.')
        toggleEnabledAction.triggered.connect(self.toggle_enable_descendants)

        autoLayoutAction = QAction('&Auto Layout', self)
        autoLayoutAction.setStatusTip('Auto-arrange the nodes.')
        autoLayoutAction.triggered.connect(self.auto_layout)

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

        debugAction = QAction('&Debug', self)
        debugAction.setShortcut('Shift+Ctrl+Alt+D')
        debugAction.setStatusTip('Debug!')
        debugAction.triggered.connect(self.debug)

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
        editMenu.addAction(expandAllAction)
        editMenu.addAction(constructExperimentAction)
        editMenu.addAction(toggleEnabledAction)
        editMenu.addAction(duplicateAction)
        editMenu.addSeparator()
        editMenu.addAction(autoLayoutAction)
        editMenu.addSeparator()
        editMenu.addAction(undoAction)
        editMenu.addAction(redoAction)

        helpMenu.addAction(debugAction)

        # Setup layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.view)
        self.hbox.setContentsMargins(0,0,0,0)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.hbox)

        self.setCentralWidget(self.main_widget)

        # Establish automatic QSettings update timer that
        # writes the node positions every 3s
        self.settings_timer = QTimer(self)
        self.settings_timer.setInterval(3000)
        self.settings_timer.timeout.connect(self.scene.save_node_positions_to_settings)
        self.settings_timer.start()

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

        # Try to check on screen changes...
    def moveEvent(self, event):
        self.scene.update_screen()
        return super(NodeWindow, self).moveEvent(event)


    def set_status(self, text, time=2000):
        self.status_bar.showMessage(text, time)

    def debug(self):
        import ipdb; ipdb.set_trace()

    def load_yaml(self, meas_file):
        self.set_status("Loading YAML configuration files...")

        self.meas_file  = meas_file

        # Perform a preliminary loading to find all of the connected files...
        _, self.filenames, self.dirname = yaml_load(self.meas_file)

        # Delay timer to avoid multiple firings
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_yaml)

        # Delay timer to avoid multiple firings
        self.ignore_file_updates = False
        self.ignore_timer = QTimer(self)
        self.ignore_timer.setSingleShot(True)
        self.ignore_timer.setInterval(1500)
        self.ignore_timer.timeout.connect(self.stop_ignoring_updates)

        # Establish File Watchers for these config files:
        self.watcher = QFileSystemWatcher()
        # Note many editors make copies and delete files.  This confuses the
        # file watchers in linux especially, so we just watch the config
        # directory for changes
        self.watcher.addPath(self.dirname)
        self.watcher.directoryChanged.connect(self.yaml_needs_update)

        self.update_timer.start()

    def stop_ignoring_updates(self):
        self.ignore_file_updates = False

    def yaml_needs_update(self, path):
        if not self.update_timer.isActive() and not self.ignore_file_updates:
            self.update_timer.start()

    def update_yaml(self):
        self.set_status("Files changed on disk, reloading.")
        self.scene.reload_yaml()

    def save(self):
        self.scene.save_for_yaml()

    def undo(self):
        self.scene.undo_stack.undo()

    def redo(self):
        self.scene.undo_stack.redo()

    def construct_experiment(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        wires = [i for i in self.scene.items() if isinstance(i, Wire)]
        create_experiment_graph(nodes, wires)

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
            if sn in graph.nodes():
                descs = descendants(graph, sn)
                items.extend(descs)

        new_status = not nodes_by_label[selected_nodes[0]].enabled

        for i in items:
            nodes_by_label[i].enabled = new_status

    def auto_layout(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        wires = [i for i in self.scene.items() if isinstance(i, Wire)]
        nodes_by_label = {i.label.toPlainText(): i for i in self.scene.items() if isinstance(i, Node)}
        graph = generate_graph(wires, dag=True)
        input_nodes = graph_input_nodes(graph)
        for input_node in input_nodes:
            pos = hierarchy_pos(graph, input_node)
            for l, p in pos.items():
                nodes_by_label[l].setPos(-p[1], p[0])

    def collapse_all(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            n.change_collapsed_state(True)

    def expand_all(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            n.change_collapsed_state(False)

    def duplicate(self):
        selected_nodes = [i for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
        self.scene.undo_stack.push(CommandDuplicateNodes(selected_nodes, self.scene))

    def cleanup(self):
        # Have to manually close proxy widgets
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            for k, v in n.parameters.items():
                pass
