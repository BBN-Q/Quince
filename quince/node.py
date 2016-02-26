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
        self.setRect(0,0,self.rect().width(),self.rect().height()+15)
        self.min_height += 15
        self.outputs[connector.name] = connector
        self.itemResize(QPointF(0.0,0.0))

    def add_input(self, connector):
        connector.setParentItem(self)
        connector.parent = self
        connector.setPos(0,30+15*(len(self.inputs)+len(self.outputs)))
        self.setRect(0,0,self.rect().width(),self.rect().height()+15)
        self.min_height += 15
        self.inputs[connector.name] = connector
        self.itemResize(QPointF(0.0,0.0))

    def add_parameter(self, param):
        param.setParentItem(self)
        param.parent = self
        self.setRect(0,0,self.rect().width(),self.rect().height()+42)
        self.min_height += 42
        param.setPos(0,30+15*(len(self.inputs)+len(self.outputs))+42*len(self.parameters))
        self.parameters[param.name] = param
        self.itemResize(QPointF(0.0,0.0))

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
                # self.scene().update_inspector_lists()
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
