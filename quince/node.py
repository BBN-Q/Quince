# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the node descriptions

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *

from .wire import *

class Node(QGraphicsRectItem):
    """docstring for Node"""
    def __init__(self, name, parent=None):
        super(Node, self).__init__(parent=parent)
        self.name = name
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.outputs = {}
        self.inputs = {}
        self.allowed_destinations = {}
        self.parameters = {}
        self.parameter_order = {}
        self.collapsed = False

        self.bg_color   = self.default_bg_color   = QColor(240,240,240,235)
        self.edge_color = self.default_edge_color = QColor(200,200,200)
        self.edge_thick = 0.75
        self.setRect(0,0,100,30)

        # Title bar
        self.title_bar = QGraphicsRectItem(parent=self)
        self.title_bar.setRect(0,0,100,20)
        self.title_color = self.default_title_color = QColor(80,80,100)
        self.label = TitleText(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.white)

        # Glossy flair
        shiny_part = QGraphicsPolygonItem(QPolygonF([QPointF(0,0), QPointF(120,0), QPointF(0,8)]),
                                          parent=self)
        shiny_part.setBrush(QBrush(QColor(200,200,250,50)))
        shiny_part.setPen(QPen(Qt.NoPen))


        # Enabled by default
        self.enabled = True

        # For PyQLab interoperability
        self.x__class__ = None
        self.x__module__ = None

        # Any additional json we should retain from PyQLab
        self.base_params = None

        if self.label.boundingRect().topRight().x() > 120:
            self.min_width = self.label.boundingRect().topRight().x()+20
            self.setRect(0,0,self.label.boundingRect().topRight().x()+20,30)
        else:
            self.min_width = 120.0

        self.min_height = 30

        # Dividing line and collapse button
        self.divider = QGraphicsLineItem(20, 0, self.rect().width()-5, 0, self)
        self.collapse_box = CollapseBox(parent=self)
        self.collapse_box.setX(10)

        # Resize Handle
        self.resize_handle = ResizeHandle(parent=self)
        self.resize_handle.setPos(self.rect().width()-8, self.rect().height()-8)

        # Disable box
        self.disable_box = None

        # Make sure things are properly sized
        self.itemResize(QPointF(0.0,0.0))

        # Synchronizing parameters
        self.changing = False

        # Render a nice Drop Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18.0)
        shadow.setOffset(0.0, 10.0)
        shadow.setColor(QColor("#99121212"))
        self.setGraphicsEffect(shadow)

        # Set up hovering
        self.setAcceptHoverEvents(True)
   
    @property
    def enabled(self):
        return self._enabled
    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        if value:
            self.bg_color = self.default_bg_color
            self.title_color = QColor(80,80,100)
        else:
            self.bg_color = QColor(140,140,140)
            self.title_color = QColor(100,100,100)
        self.update()

    def hoverEnterEvent(self, event):
        self.prev_edge_color = self.edge_color
        self.prev_edge_thick = self.edge_thick
        self.edge_color = QColor(247,247,247)
        self.edge_thick = 1.5
        self.update()

    def hoverLeaveEvent(self, event):
        self.edge_color = self.prev_edge_color
        self.edge_thick = self.prev_edge_thick
        self.update()

    def update_min_width(self):
        widths = [p.width() for p in self.parameters.values()]
        widths.extend([o.width() for o in self.outputs.values()])
        widths.extend([i.width() for i in self.inputs.values()])
        widths.append(self.label.boundingRect().topRight().x())
        self.min_width = max(widths)+20
        self.itemResize(QPointF(-100.0,-100.0))

    def value_changed(self, name):
        # Update the sweep parameters accordingly
        if self.name == "Sweep":
            stop  = self.parameters['Stop'].value()
            start = self.parameters['Start'].value()
            incr  = self.parameters['Incr.'].value()
            steps = self.parameters['Steps'].value()
            if name == "Incr.":
                if incr != 0.0:
                    steps = int(float(stop-start)/float(incr))
                    self.parameters['Steps'].set_value(steps if steps>0 else 1)
            elif name == "Steps":
                self.parameters['Incr.'].set_value((stop-start)/steps)
            else:
                self.parameters['Incr.'].set_value((stop-start)/steps)
        self.changing = False

    def add_output(self, connector):
        connector.setParentItem(self)
        connector.parent = self
        connector.setPos(self.rect().width(),30+15*(len(self.outputs)+len(self.inputs)))
        self.outputs[connector.name] = connector
        self.change_collapsed_state(self.collapsed) # Just for resizing in this case

    def add_input(self, connector):
        connector.setParentItem(self)
        connector.parent = self
        connector.setPos(0,30+15*(len(self.inputs)+len(self.outputs)))
        self.inputs[connector.name] = connector
        self.change_collapsed_state(self.collapsed) # Just for resizing in this case

    def add_parameter(self, param):
        param.setParentItem(self)
        param.parent = self
        self.parameters[param.name] = param
        self.parameter_order[len(self.parameter_order)] = param.name
        self.change_collapsed_state(self.collapsed) # Just for resizing in this case

    def change_collapsed_state(self, collapsed):
        self.collapsed = collapsed

        self.collapse_box.setRotation(0.0 if self.collapsed else 90.0)

        # Update the positions
        pos = 32+15*(len(self.inputs)+len(self.outputs))
        if len(self.parameters) > 0:
            self.divider.setY(pos)
            self.collapse_box.setY(pos)
            self.divider.setVisible(True)
            self.collapse_box.setVisible(True)
            pos += 10
        else:
            self.divider.setVisible(False)
            self.collapse_box.setVisible(False)

        for i in range(len(self.parameter_order)):
            # We completely hide parameters without inputs
            if not self.parameters[self.parameter_order[i]].has_input:
                if self.collapsed:
                    self.parameters[self.parameter_order[i]].setVisible(False)
                else:
                    self.parameters[self.parameter_order[i]].setPos(0, pos)
                    pos += self.parameters[self.parameter_order[i]].height
                    self.parameters[self.parameter_order[i]].setVisible(True)
            else:
                self.parameters[self.parameter_order[i]].setVisible(True)
                self.parameters[self.parameter_order[i]].setPos(0, pos)
                self.parameters[self.parameter_order[i]].set_collapsed(self.collapsed)
            
                if self.collapsed:
                    pos += self.parameters[self.parameter_order[i]].height_collapsed
                else:
                    pos += self.parameters[self.parameter_order[i]].height

        self.setRect(0,0,self.min_width, pos)
        self.min_height = pos
        self.update_min_width()
        self.itemResize(QPointF(0.0,0.0))
    
        for k, v in self.parameters.items():
            for w in v.wires_in:
                w.set_end(v.scenePos())

    def update_fields_from_connector(self):
        # This is peculiar to the "Sweep Nodes"
        wires_out = self.outputs['Swept Param.'].wires_out
        if len(wires_out) > 0:
            wire_end = wires_out[0].end_obj

            self.parameters['Start'].datatype = wire_end.value_box.datatype
            self.parameters['Start'].value_box.datatype  = wire_end.value_box.datatype
            self.parameters['Start'].value_box.min_value = wire_end.value_box.min_value
            self.parameters['Start'].value_box.max_value = wire_end.value_box.max_value
            self.parameters['Start'].value_box.increment = wire_end.value_box.increment
            self.parameters['Start'].value_box.snap      = wire_end.value_box.snap
            self.parameters['Start'].value_box.set_value(self.parameters['Start'].value())

            self.parameters['Stop'].datatype = wire_end.value_box.datatype
            self.parameters['Stop'].value_box.datatype  = wire_end.value_box.datatype
            self.parameters['Stop'].value_box.min_value = wire_end.value_box.min_value
            self.parameters['Stop'].value_box.max_value = wire_end.value_box.max_value
            self.parameters['Stop'].value_box.increment = wire_end.value_box.increment
            self.parameters['Stop'].value_box.snap      = wire_end.value_box.snap
            self.parameters['Stop'].value_box.set_value(self.parameters['Stop'].value())

            self.parameters['Incr.'].datatype = wire_end.value_box.datatype
            self.parameters['Incr.'].value_box.datatype  = wire_end.value_box.datatype
            self.parameters['Incr.'].value_box.min_value = -2*abs(wire_end.value_box.max_value)
            self.parameters['Incr.'].value_box.max_value = 2*abs(wire_end.value_box.max_value)
            self.parameters['Incr.'].value_box.increment = wire_end.value_box.increment
            self.parameters['Incr.'].value_box.snap      = wire_end.value_box.snap
            self.parameters['Incr.'].value_box.set_value(self.parameters['Incr.'].value())
        
    def update_parameters_from(self, other_node):
        # Make sure they are of the same type
        if other_node.name == self.name:
            for k, v in other_node.parameters.items():
                self.parameters[k].set_value(v.value())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for k, v in self.outputs.items():
                v.setX(self.rect().width())
                for w in v.wires_out:
                    w.set_start(v.pos()+value)
            for k, v in self.inputs.items():
                for w in v.wires_in:
                    w.set_end(v.pos()+value)
            for k, v in self.parameters.items():
                for w in v.wires_in:
                    w.set_end(v.pos()+value)
        elif change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.edge_color = QColor(247,217,17)
                self.edge_thick = 1.25
                self.title_color = QColor(110,110,80)
                self.prev_edge_color = self.edge_color
                self.prev_edge_thick = self.edge_thick
            else:
                self.edge_color = self.default_edge_color
                self.edge_thick = 0.75
                self.title_color = self.default_title_color
        return QGraphicsRectItem.itemChange(self, change, value)

    def itemResize(self, delta):
        # Keep track of actual change
        actual_delta = QPointF(0,0)

        r = self.rect()
        if r.width()+delta.x() >= self.min_width:
            r.adjust(0, 0, delta.x(), 0)
            actual_delta.setX(delta.x())

        if r.height()+delta.y() >= self.min_height:
            r.adjust(0, 0, 0, delta.y())
            actual_delta.setY(delta.y())

        self.setRect(r)
        delta.setY(0.0)

        if hasattr(self, 'resize_handle'):
            self.resize_handle.setPos(self.rect().width()-8, self.rect().height()-8)
        if hasattr(self, 'title_bar'):
            self.title_bar.setRect(0,0,self.rect().width(),20)

        conn_delta = actual_delta.toPoint()
        conn_delta.setY(0.0)

        self.divider.setLine(20, 0, self.rect().width()-5, 0)

        # Move the outputs
        for k, v in self.outputs.items():
            v.setX(self.rect().width())
            for w in v.wires_out:
                w.set_start(v.scenePos()+conn_delta)

        # Resize the parameters
        for k, v in self.parameters.items():
            v.set_box_width(self.rect().width())

        return actual_delta

    def create_wire(self, parent):
    	return Wire(parent)

    def paint(self, painter, options, widget):
        painter.setPen(QPen(self.edge_color, self.edge_thick))
        self.title_bar.setPen(QPen(self.edge_color, self.edge_thick))
        self.title_bar.setBrush(QBrush(self.title_color))
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRoundedRect(self.rect(), 5.0, 5.0)

    def dict_repr(self):
        if self.base_params is not None:
            dict_repr = dict(self.base_params)
        else:
            dict_repr = {}

        # Find the name of the source connectors (assuming one connection)
        # The default connector name is "source", in which case data_source
        # is just the name of the node. Otherwise, we return a data_source
        # of the form "node_name:connector_name", e.g.
        # "averager:partial_averages"

        if ('sink' in self.inputs.keys()) and len(self.inputs['sink'].wires_in) > 0:
            connector = self.inputs['sink'].wires_in[0].start_obj
            node_name = connector.parent.label.toPlainText()
            conn_name = connector.name
            
            if conn_name == "source":
                dict_repr['data_source'] = node_name
            else:
                dict_repr['data_source'] = node_name + ":" + conn_name
        else:
            dict_repr['data_source'] = ""

        dict_repr['label']       = self.label.toPlainText()
        dict_repr['enabled']     = self.enabled
        dict_repr['x__class__']  = self.x__class__
        dict_repr['x__module__'] = self.x__module__
        return dict_repr

class TitleText(QGraphicsTextItem):
    '''QGraphicsTextItem with textChanged() signal.'''
    textChanged = Signal(str)

    def __init__(self, text, parent=None):
        super(TitleText, self).__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self._value = text
        self.parent = parent

    def setPlainText(self, text):
        if hasattr(self.scene(), 'items'):
            nodes = [i for i in self.scene().items() if isinstance(i, Node)]
            nodes.remove(self.parent)
            node_names = [n.label.toPlainText() for n in nodes]
            if text in node_names:
                self.scene().window.set_status("Node name already exists")
            else:
                # self.scene().inspector_change_name(self._value, text)
                self._value = text
            self.textChanged.emit(self.toPlainText())
        else:
            self._value = text
        
        super(TitleText, self).setPlainText(self._value)

    def focusOutEvent (self, event):
        self.setPlainText(self.toPlainText())
        super(TitleText, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            c = self.textCursor()
            c.clearSelection()
            self.setTextCursor(c)
            self.clearFocus()
        else:
            return super(TitleText, self).keyPressEvent(event)

class ResizeHandle(QGraphicsRectItem):
    """docstring for ResizeHandle"""
    def __init__(self, parent=None):
        super(ResizeHandle, self).__init__()
        self.dragging = False
        self.parent = parent
        self.drag_start = None
        self.setParentItem(parent)
        self.setRect(0,0,5,5)
        self.setBrush(QColor(20,20,20))

    def mousePressEvent(self, event):
        self.dragging = True
        self.drag_start = event.scenePos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.scenePos() - self.drag_start
            actual_delta = self.parent.itemResize(delta)
            self.drag_start = self.drag_start + actual_delta

    def mouseReleaseEvent(self, event):
        self.dragging = False

class CollapseBox(QGraphicsItem):
    """docstring for CollapseBox"""
    def __init__(self, parent=None):
        super(CollapseBox, self).__init__(parent=parent)
        self.parent = parent
        self.clicking = False
        self.height = 8
        self.width = 8
    
        self.setRotation(90.0)

    def paint(self, painter, options, widget):
        # Draw our triangle    
        painter.setPen(QPen(QColor(0,0,0), 1.0))
        painter.setBrush(QColor(160,200,220))
        
        path = QPainterPath()
        path.moveTo(-4,4)
        path.lineTo(4,0)
        path.lineTo(-4,-4)
        path.lineTo(-4,4)
        painter.drawPath(path)

    def boundingRect(self):
        return QRectF(QPointF(-5,-6), QSizeF(15, 15))

    def shape(self):
        p = QPainterPath()
        p.addRect(-5, -6, 15, 15)
        return p

    def mousePressEvent(self, event):
        self.clicking = True

    def mouseReleaseEvent(self, event):
        if self.clicking:
            self.parent.change_collapsed_state(not self.parent.collapsed)
            self.setRotation(0.0 if self.parent.collapsed else 90.0)
        self.clicking = False

class CommandAddNode(QUndoCommand):
    def __init__(self, node_name, create_func, scene):
        super(CommandAddNode, self).__init__("Add node {}".format(node_name))
        self.create_func = create_func
        self.scene = scene
    def redo(self):
        self.new_node = self.create_func()
    def undo(self):
        self.scene.removeItem(self.new_node)

class CommandDeleteNodes(QUndoCommand):
    def __init__(self, nodes, scene):
        super(CommandDeleteNodes, self).__init__("Delete nodes {}".format(",".join([n.name for n in nodes])))
        self.scene = scene
        self.nodes = nodes
    
    def redo(self):
        self.output_wires    = []
        self.input_wires     = []
        self.parameter_wires = []

        for node in self.nodes:
            for k, v in node.outputs.items():
                for w in v.wires_out:
                    w.end_obj.wires_in.pop(w.end_obj.wires_in.index(w))
                    self.output_wires.append(w)
                    self.scene.removeItem(w)
            for k, v in node.inputs.items():
                for w in v.wires_in:
                    w.start_obj.wires_out.pop(w.start_obj.wires_out.index(w))
                    self.input_wires.append(w)
                    self.scene.removeItem(w)
            for k, v in node.parameters.items():
                for w in v.wires_in:
                    w.end_obj.wires_in.pop(w.end_obj.wires_in.index(w))
                    self.parameter_wires.append(w)
                    self.scene.removeItem(w)
            self.scene.removeItem(node)
            node.update()
        self.scene.update()

    def undo(self):
        for node in self.nodes:
            self.scene.addItem(node)
        for w in self.output_wires:
            w.end_obj.wires_in.append(w)
            self.scene.addItem(w)
        for w in self.input_wires:
            w.start_obj.wires_out.append(w)
            self.scene.addItem(w)
        for w in self.parameter_wires:
            w.end_obj.wires_in.append(w)
            self.scene.addItem(w)
        self.output_wires    = []
        self.input_wires     = []
        self.parameter_wires = []
        self.scene.update()