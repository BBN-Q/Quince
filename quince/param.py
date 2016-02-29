# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the parameter descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import os

class Parameter(QGraphicsEllipseItem):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        rad = 5
        super(Parameter, self).__init__(-rad, -rad, 2*rad, 2*rad, parent=parent)

        self.has_input   = True # Do we draw the connector?
        self.interactive = True # Can we modify the value?
        
        self.setBrush(QBrush(QColor(200,200,240)))
        self.setPen(Qt.black)
        self.setZValue(1)

        self.height = 42
        self.height_collapsed = 15 

        self.temp_wire = None
        self.wires_in  = []
        self.wires_out = []

        # Text label and area
        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(5,-10)

        # Value Box
        self.value_box = None

    def set_changed_flag(self):
        # Would prefer to use signals/slots, but that's apparently too heavy for QGraphics
        # Instead we add the name of the changed parameter to the list
        if self.parent is not None and not self.parent.changing:
            self.parent.changing = True
            self.parent.value_changed( self.name )

    def set_interactive(self, value):
        self.interactive = value
        self.value_box.interactive = value

    def set_collapsed(self, collapsed):
        self.collapsed = collapsed
        self.value_box.setVisible(not self.collapsed)

    def width(self):
        return self.label.boundingRect().topRight().x()

    def set_box_width(self, width):
        self.value_box.set_box_width(width)

    def value(self):
        return self.value_box.value()

    def set_value(self, value):
        self.value_box.set_value(float(value))
        self.set_changed_flag()

    def paint(self, painter, options, widget):
        if self.has_input:
            super(Parameter, self).paint(painter, options, widget)

class NumericalParameter(Parameter):
    """docstring for Parameter"""
    def __init__(self, name, datatype, min_value, max_value,
                 increment, snap, parent=None):
        super(NumericalParameter, self).__init__(name, parent=parent)
        # Slider Box
        self.datatype = datatype
        self.value_box = SliderBox(
            datatype, min_value, max_value, increment, snap,
            parent=self)
        
    def set_value(self, value):
        self.value_box.set_value(self.datatype(value))
        self.set_changed_flag()

class StringParameter(Parameter):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        super(StringParameter, self).__init__(name, parent=parent)
        self.value_box = StringBox(parent=self)
        self.parent = parent
        
    def set_value(self, value):
        self.value_box.set_value(value)

class ComboParameter(StringParameter):
    """docstring for Parameter"""
    def __init__(self, name, values, parent=None):
        super(ComboParameter, self).__init__(name, parent=parent)
        self.value_box = ComboBox(values, parent=self)

class BooleanParameter(Parameter):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        super(BooleanParameter, self).__init__(name, parent=parent)
        self.value_box = CheckBox(parent=self)
        self.parent = parent
        self.height = 15
        self.height_collapsed = 15

    def width(self):
        return self.label.boundingRect().topRight().x() + 18

class FilenameParameter(StringParameter):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        super(FilenameParameter, self).__init__(name, parent=parent)
        # SliderBox
        self.value_box = FilenameBox(parent=self)
        
    def width(self):
        return self.label.boundingRect().topRight().x() + 35

class SliderBox(QGraphicsRectItem):
    """docstring for SliderBox"""

    def __init__(self, datatype, min_value, max_value, increment, snap, parent=None):
        super(SliderBox, self).__init__(parent=parent)
        self.parent = parent
        self.dragging = False
        self.value_changed = False

        self.interactive = True

        self.datatype  = datatype
        self.min_value = min_value
        self.max_value = max_value
        self.increment = increment
        self.snap      = snap
        self._value = min_value

        self.height = 14
        self.rect_radius = 7.0
        self.control_distance = 0.55228*self.rect_radius
        self.setRect(3,15,94,self.height)

        self.label = ValueBoxText(self.textFromValue(self._value), parent=self)
        label_width = self.label.boundingRect().topRight().x()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)

    def paint(self, painter, options, widget):
        # Background object is a rounded rectangle
        painter.RenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(220,220,220)))
        painter.setPen(QPen(QColor(200,200,200), 0.75))
        painter.drawRoundedRect(self.rect(), self.rect_radius, self.rect_radius)

        # Draw the bar using a round capped line
        painter.setPen(QPen(QColor(160,200,220), self.height, cap=Qt.RoundCap))
        path = QPainterPath()
        path.moveTo(3+self.rect_radius, 15 + 0.5*self.height)
        fill_size = (self.rect().width()-2*self.rect_radius)*(self._value-self.min_value)/(self.max_value-self.min_value)
        path.lineTo(3+self.rect_radius+fill_size, 7.5 + 0.5+self.height)
        painter.drawPath(path)

    def valueFromText(self, text):
        try:
            if self.datatype is int:
                val =  int(str(text))
            else:
                val = float(str(text))
            return val
        except:
            self.scene().window.set_status("Got unreasonable input...")
            return self._value

    def textFromValue(self, value):
        if self.datatype is int:
            return ("{:d}".format(value))
        else:
            return ("{:.4g}".format(value))

    def set_value(self, val):
        changed = False
        val = self.valueFromText(val)
        if val >= self.min_value and val <= self.max_value:
            if self.snap:
                val = (val/self.snap)*self.snap
            self._value = self.datatype(val)
            changed = True
            
        self.label.setPlainText(self.textFromValue(self._value))
        self.refresh_label()
        self.update()
        if changed:
            self.parent.set_changed_flag()

    def refresh_label(self):
        label_width = self.label.boundingRect().topRight().x()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)
        self.update()

    def value(self):
        return self._value

    def set_box_width(self, width):
        self.setRect(3,15, width-6, self.height)
        label_width = self.label.boundingRect().topRight().x()
        self.label.clip_text()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)

    def mousePressEvent(self, event):
        if self.interactive:
            self.dragging = True
            self.original_value = self._value
            self.drag_start = event.scenePos()
        else:
            super(SliderBox, self).mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        if self.interactive:
            if self.dragging:
                delta = event.scenePos() - self.drag_start
                value_change = self.increment*int(delta.x()/10.0)
                if value_change != 0.0:
                    self.value_changed = True
                self.set_value(self.original_value + value_change)
        else:
            super(SliderBox, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.interactive:
            self.dragging = False
            if not self.value_changed:
                self.label.setPos(3+5,15-5)
                self.label.set_text_interaction(True)
            self.value_changed = False
        else:
            super(SliderBox, self).mouseMoveEvent(event)

class StringBox(QGraphicsRectItem):
    """docstring for SliderBox"""
    def __init__(self, parent=None):
        super(StringBox, self).__init__(parent=parent)
        self.clicked = False
        self._value = ""

        self.height = 14
        self.rect_radius = 7.0
        self.control_distance = 0.55228*self.rect_radius
        self.setRect(3,15,94,self.height)

        self.label = ValueBoxText(self._value, parent=self)
        label_width = self.label.boundingRect().topRight().x()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)

    def paint(self, painter, options, widget):
        # Background object is a rounded rectangle
        painter.RenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(220,220,220)))
        painter.setPen(QPen(QColor(200,200,200), 0.75))
        painter.drawRoundedRect(self.rect(), self.rect_radius, self.rect_radius)

    def set_value(self, value):
        self._value = value
        self.label.full_text = value
        self.label.setPlainText(value)
        self.label.clip_text()
        self.refresh_label()
        self.update()
        if hasattr(self, 'parent'):
            self.parent.set_changed_flag()

    def refresh_label(self):
        label_width = self.label.boundingRect().topRight().x()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)
        self.update()

    def value(self):
        return self._value

    def set_box_width(self, width):
        self.setRect(3,15, width-6, self.height)
        self.label.clip_text()
        self.refresh_label()

    def mousePressEvent(self, event):
        self.clicked = True

    def mouseReleaseEvent(self, event):
        if self.clicked:
            self.label.setPos(3+5,15-5)
            self.label.set_text_interaction(True)
        self.clicked = False

class FilenameBox(StringBox):
    """docstring for FilenameBox"""
    def __init__(self, parent=None):
        super(FilenameBox, self).__init__(parent=parent)
        self.browse_button = QGraphicsRectItem(self.rect().width()-28, -3, 30, 12, parent=self)
        self.browse_button.setBrush(QBrush(QColor(220,220,220)))
        self.browse_button.mousePressEvent = lambda e: self.save_file()
        # self.browse_button.mouseReleaseEvent = lambda e: self.save_file()

    def save_file(self):
        path = os.path.dirname(os.path.realpath(__file__))
        fn = QFileDialog.getSaveFileName(None, 'Save Results As', path)
        self.set_value(fn[0])
        self.label.clip_text()
        self.refresh_label()

    def refresh_label(self):
        label_width = self.label.boundingRect().topRight().x()
        self.label.setPos(3+0.5*self.rect().width()-0.5*label_width,15-5)
        self.browse_button.setRect(self.rect().width()-28, -3, 30, 12)
        self.update()

class ComboBox(StringBox):
    """docstring for ComboBox"""
    def __init__(self, values, parent=None):
        super(ComboBox, self).__init__(parent=parent)
        self.menu = QMenu(self.scene())
        self.values = values

    def menu_changed(self, action):
        self.set_value(action.data())

    def mousePressEvent(self, event):
        self.clicked = True

    def mouseReleaseEvent(self, event):
        if self.clicked:
            menu = QMenu()
            for v in self.values:
                act = QAction(v, self.scene())
                act.setData(v)
                menu.addAction(act)
            menu.triggered.connect(self.menu_changed)
            menu.exec_(event.screenPos())
        self.clicked = False
        
class CheckBox(QGraphicsRectItem):
    """docstring for CheckBox"""
    def __init__(self, parent=None):
        super(CheckBox, self).__init__(parent=parent)
        self.parent = parent
        self.setRect(self.rect().width()-17, -3, 13, 13)
        self.unchecked_brush = QBrush(QColor(220,220,220))
        self.checked_brush = QBrush(QColor(40,40,40))
        self.setBrush(self.unchecked_brush)
        self._value = False
        self.clicked = False

    def set_box_width(self, width):
        self.setRect(width-17, -3, 13, 13)

    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        if self._value:
            self.setBrush(self.checked_brush)
        else:
            self.setBrush(self.unchecked_brush)

    def mousePressEvent(self, event):
        self.clicked = True

    def mouseReleaseEvent(self, event):
        if self.clicked:
            self.set_value(not self._value)
        self.clicked = False

class ValueBoxText(QGraphicsTextItem):
    """docstring for ValueBoxText"""
    def __init__(self, string, parent=None):
        super(ValueBoxText, self).__init__(string, parent=parent)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.ItemIsFocusable = True
        self.parent = parent
        self.full_text = string
        self.clip_text()

    def set_text_interaction(self, value):
        if value and (self.textInteractionFlags() == Qt.NoTextInteraction):
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setPlainText(self.full_text)
            self.setFocus(Qt.MouseFocusReason)
            self.setSelected(True)
            c = self.textCursor()
            c.select(QTextCursor.Document)
            self.setTextCursor(c)
        elif not value and (self.textInteractionFlags() == Qt.TextEditorInteraction):
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            c = self.textCursor()
            c.clearSelection()
            self.setTextCursor(c)
            self.clearFocus()

    def clip_text(self):
        if self.parent.rect().width() < self.boundingRect().topRight().x():
            clipped = self.full_text[:int(self.parent.rect().width()/7)-3]
            if int(self.parent.rect().width()/6)-3 == len(self.full_text)-1:
                self.setPlainText(clipped)
            else:
                self.setPlainText(clipped+"...")

    def focusOutEvent(self, event):
        self.set_text_interaction(False)
        self.parent.set_value(self.toPlainText())
        # self.full_text = self.toPlainText()
        self.clip_text()
        self.parent.refresh_label()
        return super(ValueBoxText, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.set_text_interaction(False)
            self.parent.set_value(self.toPlainText())
            self.full_text = self.toPlainText()
            self.clip_text()
            self.parent.refresh_label()
        else:
            return super(ValueBoxText, self).keyPressEvent(event)
