# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the node descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

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
        self.parameters = {}
        self.parameter_order = {}
        self.collapsed = False

        self.bg_color = QColor(240,240,240)
        self.edge_color = QColor(200,200,200)
        self.edge_color_selected = QColor(247,217,17)
        self.setRect(0,0,100,30)
        self.setBrush(QBrush(self.bg_color))
        self.setPen(QPen(QColor(200,200,200), 0.75))

        # Title bar
        self.title_bar = QGraphicsRectItem(parent=self)
        self.title_bar.setRect(0,0,100,20)
        self.title_color = QColor(80,80,100)
        self.title_color_selected = QColor(110,110,80)
        self.title_bar.setBrush(QBrush(self.title_color))
        self.title_bar.setPen(QPen(QColor(200,200,200), 0.75))
        self.label = TitleText(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.white)

        if self.label.boundingRect().topRight().x() > 80:
            self.min_width = self.label.boundingRect().topRight().x()+20
            self.setRect(0,0,self.label.boundingRect().topRight().x()+20,30)
        else:
            self.min_width = 80.0

        self.min_height = 30

        # Dividing line and collapse button
        self.divider = QGraphicsLineItem(20, 0, self.rect().width()-5, 0, self)
        self.collapse_box = CollapseBox(parent=self)
        self.collapse_box.setX(10)

        # Resize Handle
        self.resize_handle = ResizeHandle(parent=self)
        self.resize_handle.setPos(self.rect().width()-8, self.rect().height()-8)

        # Remove box
        self.remove_box = RemoveBox(parent=self)
        self.remove_box.setPos(self.rect().width()-13, 5)

        # Disable box
        self.disable_box = None

        # Make sure things are properly sized
        self.itemResize(QPointF(0.0,0.0))

        # Synchronizing parameters
        self.changing = False
   
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

    def set_title_color(self, color):
        self.title_color = color
        self.title_bar.setBrush(QBrush(color))

    def set_bg_color(self, color):
        self.bg_color = color
        self.setBrush(QBrush(color))

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
        if hasattr(self, 'remove_box'):
            self.remove_box.setPos(self.rect().width()-13, 5)

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

    def disconnect(self):
        for k, v in self.outputs.items():
            for w in v.wires_out:
                w.start_obj = None
        for k, v in self.inputs.items():
            for w in v.wires_in:
                w.end_obj = None
        for k, v in self.parameters.items():
            for w in v.wires_in:
                w.end_obj = None
        self.scene().clear_wires(only_clear_orphaned=True)

    def create_wire(self, parent):
    	return Wire(parent)

    def paint(self, painter, options, widget):
        if self.isSelected():
            painter.setPen(QPen(self.edge_color_selected, 1.25))
            self.title_bar.setPen(QPen(self.edge_color_selected, 1.25))
            self.title_bar.setBrush(QBrush(self.title_color_selected))
        else:
            painter.setPen(QPen(self.edge_color, 0.75))
            self.title_bar.setPen(QPen(self.edge_color, 0.75))
            self.title_bar.setBrush(QBrush(self.title_color))
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRoundedRect(self.rect(), 5.0, 5.0)

    def dict_repr(self):
        dat = {}
        dat['label'] = self.label.toPlainText()
        dat['name'] = self.name
        params = {}
        for k, v in self.parameters.items():
            params[k] = v.value()
        dat['params'] = params
        dat['pos'] = [self.scenePos().x(), self.scenePos().y()]
        return dat

    def matlab_repr(self):
        params = {}
        for k, v in self.parameters.items():
            params[k] = v.value()

        params['deviceName'] = self.name
        return params

class TitleText(QGraphicsTextItem):
    '''QGraphicsTextItem with textChanged() signal.'''
    textChanged = pyqtSignal(str)

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
                self.scene().inspector_change_name(self._value, text)
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

class RemoveBox(QGraphicsRectItem):
    """docstring for RemoveBox"""
    def __init__(self, parent=None):
        super(RemoveBox, self).__init__(parent=parent)
        self.parent = parent
        self.setRect(0,0,10,10)
        self.setBrush(QColor(60,60,60))
        self.setPen(QPen(Qt.black, 1.0))
        self.close_started = False
    
    def mousePressEvent(self, event):
        self.close_started = True

    def mouseReleaseEvent(self, event):
        self.parent.disconnect()
        self.scene().removeItem(self.parent)

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