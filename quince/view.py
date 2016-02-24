# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the windows, view, and scene descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import *
from PyQt5.QtWidgets import *

from functools import partial
import json
import glob
import os.path

from .node import *
from .wire import *
from .param import *
from .graph import *
from .util import *

class NodeScene(QGraphicsScene):
    """docstring for NodeScene"""
    def __init__(self):
        super(NodeScene, self).__init__()
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

    def contextMenuEvent(self, event):
        self.last_click = event.scenePos()
        self.menu.exec_(event.screenPos())

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
                            pp = StringParameter(p['name'])
                        node.add_parameter(pp)
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
                action.triggered.connect(func)
                self.sub_menus[cat].addAction(action)

        node_files = sorted(glob.glob('nodes/*/*.json'))
        categories = set([os.path.basename(os.path.dirname(nf)) for nf in node_files])
        
        for cat in categories:
            sm = self.menu.addMenu(cat)
            self.sub_menus[cat] = sm

        for nf in node_files:
            parse_node_file(nf)

    def load(self, filename):
        with open(filename, 'r') as df:

            # Clear scene
            nodes = [i for i in self.items() if isinstance(i, Node)]
            wires = [i for i in self.items() if isinstance(i, Wire)]
            for o in nodes+wires:
                self.removeItem(o)

            data = json.load(df)
            nodes = data['nodes']
            wires = data['wires']

            new_nodes = {} # Keep track of nodes we create

            for n in nodes:
                create_node_func_name = "create_"+("".join(n['name'].split()))
                if hasattr(self, create_node_func_name):
                    if n['label'] not in new_nodes.keys():
                        new_node = getattr(self, create_node_func_name)()
                        new_node.setPos(float(n['pos'][0]), float(n['pos'][1]))
                        for k, v in n['params'].items():
                            new_node.parameters[k].set_value(v)
                        new_node.label.setPlainText(n['label'])
                        new_nodes[n['label']] = new_node
                    else:
                        print("Node cannot be named {}, label already in use".format(n['label']))
                else:
                    print("Could not load node of type {}, please check nodes directory.".format(n['name']))

            for w in wires:
                # Instantiate a little later
                new_wire = None

                start_node_name = w['start']['node']
                end_node_name   = w['end']['node']
                start_conn_name = w['start']['connector_name']
                end_conn_name   = w['end']['connector_name']

                start_node = new_nodes[start_node_name]
                end_node   = new_nodes[end_node_name]

                # Find our beginning connector
                if start_conn_name in start_node.outputs.keys():
                    new_wire = Wire(start_node.outputs[start_conn_name])
                    self.addItem(new_wire)
                    new_wire.set_start(start_node.outputs[start_conn_name].scenePos())
                    start_node.outputs[start_conn_name].wires_out.append(new_wire)
                    
                    # Find our end connector
                    if end_conn_name in end_node.inputs.keys():
                        new_wire.end_obj = end_node.inputs[end_conn_name]
                        new_wire.set_end(end_node.inputs[end_conn_name].scenePos())
                        end_node.inputs[end_conn_name].wires_in.append(new_wire)
                    elif end_conn_name in end_node.parameters.keys():
                        new_wire.end_obj = end_node.parameters[end_conn_name]
                        new_wire.set_end(end_node.parameters[end_conn_name].scenePos())
                        end_node.parameters[end_conn_name].wires_in.append(new_wire)
                    else:
                        print("Could not find input {} on node {}.".format(end_conn_name, end_node_name))
                else:
                    print("Could not find output {} on node {}.".format(start_conn_name, start_node_name))

    def save(self, filename):
        with open(filename, 'w') as df:
            nodes = [i for i in self.items() if isinstance(i, Node)]
            wires = [i for i in self.items() if isinstance(i, Wire)]
            
            data = {}
            data['nodes'] = [n.dict_repr() for n in nodes]
            data['wires'] = [n.dict_repr() for n in wires]
            json.dump(data, df, sort_keys=True, indent=4, separators=(',', ': '))

    def create_node_by_name(self, name):
        create_node_func_name = "create_"+("".join(name.split()))
        if hasattr(self, create_node_func_name):
            new_node = getattr(self, create_node_func_name)()
            return new_node
        else:
            print("Could not create a node of the requested type.")
            return None

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

    def mousePressEvent(self, event):
        if (event.button() == Qt.MidButton) or (event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            return super(NodeView, self).mousePressEvent(fake)
        else:
            return super(NodeView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MidButton) or (event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier):
            self.setDragMode(QGraphicsView.NoDrag)
            fake = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            return super(NodeView, self).mouseReleaseEvent(fake)
        else:
            return super(NodeView, self).mouseReleaseEvent(event)

class NodeWindow(QMainWindow):
    """docstring for NodeWindow"""
    def __init__(self, parent=None):
        super(NodeWindow, self).__init__(parent=parent)
        self.setWindowTitle("Nodes")
        self.setGeometry(50,50,800,600)
        
        # Setup graphics
        self.scene = NodeScene()
        self.view  = NodeView(self.scene)

        # Setup menu
        self.statusBar()

        exitAction = QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QApplication.instance().quit)

        saveAction = QAction('&Save', self)        
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save')
        saveAction.triggered.connect(self.save)

        openAction = QAction('&Open', self)        
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open')
        openAction.triggered.connect(self.load)

        selectAllAction = QAction('&Select All', self)        
        selectAllAction.setShortcut('Ctrl+A')
        selectAllAction.setStatusTip('Select All')
        selectAllAction.triggered.connect(self.select_all)

        selectAllConnectedAction = QAction('&Select All Connected', self)        
        selectAllConnectedAction.setShortcut('Shift+Ctrl+A')
        selectAllConnectedAction.setStatusTip('Select All Connected')
        selectAllConnectedAction.triggered.connect(self.select_all_connected)

        duplicateAction = QAction('&Duplicate', self)        
        duplicateAction.setShortcut('Ctrl+D')
        duplicateAction.setStatusTip('Duplicate')
        duplicateAction.triggered.connect(self.duplicate)

        fileMenu = self.menuBar().addMenu('&File')
        editMenu = self.menuBar().addMenu('&Edit')
        helpMenu = self.menuBar().addMenu('&Help')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(openAction)
        editMenu.addAction(selectAllAction)
        editMenu.addAction(selectAllConnectedAction)
        editMenu.addAction(duplicateAction)

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

        svgrend =  QSvgRenderer("assets/quince.svg")
        self.svgitem = QGraphicsSvgItem()
        self.svgitem.setSharedRenderer(svgrend)
        self.scene.addItem(self.svgitem)
        self.svgitem.setScale(0.5)
        self.svgitem.setPos(self.svgitem.pos().x()-self.svgitem.boundingRect().width()/4, 
                            self.svgitem.pos().y()-self.svgitem.boundingRect().height()/4)

        self.draw_i = 0
        self.increment = 15
        self.duration = 1600

        self.timer = QTimer()
        self.timer.timeout.connect(self.advance)
        self.timer.start(self.increment)

    def advance(self):
        if self.draw_i < self.duration:
            self.svgitem.setOpacity(1.0-float(self.draw_i)/self.duration)
            self.draw_i += self.increment
            # self.increment += 0.1
        else:  
            self.timer.stop()
            self.scene.removeItem(self.svgitem)

    def load(self):
        path = os.path.dirname(os.path.realpath(__file__))
        fn = QFileDialog.getOpenFileName(self, 'Load Graph', path)
        if fn[0] != '':
            self.scene.load(fn[0])

    def save(self):
        path = os.path.dirname(os.path.realpath(__file__))
        fn = QFileDialog.getSaveFileName(self, 'Save Graph', path)
        if fn[0] != '':
            self.scene.save(fn[0])

    def select_all(self):
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            n.setSelected(True)

    def select_all_connected(self):
        selected_nodes = [i.label.toPlainText() for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
        wires = [i for i in self.scene.items() if isinstance(i, Wire)]
        nodes_by_label = {i.label.toPlainText(): i for i in self.scene.items() if isinstance(i, Node)}
        graph = qg.generate_graph(wires)

        items = []
        for sn in selected_nodes:
            sub_graph_items = qg.items_on_subgraph(graph, sn)
            items.extend(sub_graph_items)

        for i in items:
            nodes_by_label[i].setSelected(True)

    def duplicate(self):
        selected_nodes = [i for i in self.scene.items() if isinstance(i, Node) and i.isSelected()]
        old_to_new = {}
        
        for sn in selected_nodes:
            node_names = [i.label.toPlainText() for i in self.scene.items() if isinstance(i, Node)]

            new_node = self.scene.create_node_by_name(sn.name)
            nan = next_available_name(node_names, strip_numbers(sn.label.toPlainText()))
            new_node.label.setPlainText(nan)

            # Set parameters from old
            new_node.update_parameters_from(sn)

            # Update the mapping
            old_to_new[sn] = new_node

            # Stagger and update the selection to include the new nodes
            new_node.setPos(sn.pos()+QPointF(20,20))
            sn.setSelected(False)
            new_node.setSelected(True)

        # Rewire the new nodes according to the old nodes
        for sn in selected_nodes:
            new_node = old_to_new[sn]

            for k, v in sn.outputs.items():
                for w in v.wires_out:
                    # Create the wire and set the start
                    new_wire = Wire(new_node.outputs[w.start_obj.name])
                    
                    new_wire.set_start(new_node.outputs[w.start_obj.name].scenePos())
                    new_node.outputs[w.start_obj.name].wires_out.append(new_wire)

                    # set the end of the wire
                    if w.end_obj.parent in old_to_new:
                        end_conn_name = w.end_obj.name
                        end_node = old_to_new[w.end_obj.parent]
                        if end_conn_name in end_node.inputs.keys():
                            new_wire.end_obj = end_node.inputs[end_conn_name]
                            new_wire.set_end(end_node.inputs[end_conn_name].scenePos())
                            end_node.inputs[end_conn_name].wires_in.append(new_wire)
                        elif end_conn_name in end_node.parameters.keys():
                            new_wire.end_obj = end_node.parameters[end_conn_name]
                            new_wire.set_end(end_node.parameters[end_conn_name].scenePos())
                            end_node.parameters[end_conn_name].wires_in.append(new_wire)

                        self.scene.addItem(new_wire)


    def cleanup(self):
        # Have to manually close proxy widgets
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for n in nodes:
            for k, v in n.parameters.items():
                pass