# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the parameter descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class Parameter(QGraphicsEllipseItem):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        rad = 5
        super(Parameter, self).__init__(-rad, -rad, 2*rad, 2*rad, parent=parent)
        
        self.setBrush(QBrush(QColor(200,200,240)))
        self.setPen(Qt.black)
        self.setZValue(1)

        self.temp_wire = None
        self.wires_in  = []
        self.wires_out = []

        # Text label and area
        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(5,-10)

        # Value Box
        self.value_box = None

    def set_box_width(self, width):
        self.value_box.set_box_width(width)

    def value(self):
        return self.value_box.value()

    def set_value(self, value):
        self.value_box.set_value(float(value))

class NumericalParameter(Parameter):
    """docstring for Parameter"""
    def __init__(self, name, datatype, min_value, max_value,
                 increment, snap, parent=None):
        super(NumericalParameter, self).__init__(name, parent=parent)
        # Slider Box
        self.value_box = SliderBox(
            datatype, min_value, max_value, increment, snap,
            parent=self)

class StringParameter(Parameter):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        super(StringParameter, self).__init__(name, parent=parent)
        # SliderBox
        self.value_box = StringBox(parent=self)

    def set_value(self, value):
        self.value_box.set_value(value)

class FilenameParameter(StringParameter):
    """docstring for Parameter"""
    def __init__(self, name, parent=None):
        super(FilenameParameter, self).__init__(name, parent=parent)
        # SliderBox
        self.value_box = FilenameBox(parent=self)

class SliderBox(QGraphicsRectItem):
    """docstring for SliderBox"""
    def __init__(self, datatype, min_value, max_value, increment, snap, parent=None):
        super(SliderBox, self).__init__(parent=parent)
        self.parent = parent
        self.dragging = False
        self.value_changed = False

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
        fill_size = (self.rect().width()-2*self.rect_radius)*(self._value-self.min_value)/self.max_value
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
        val = self.valueFromText(val)
        if val >= self.min_value and val <= self.max_value:
            if self.snap:
                val = (val/self.snap)*self.snap
            self._value = self.datatype(val)
            
        self.label.setPlainText(self.textFromValue(self._value))
        self.refresh_label()
        self.update()

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
        self.dragging = True
        self.original_value = self._value
        self.drag_start = event.scenePos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.scenePos() - self.drag_start
            value_change = self.increment*int(delta.x()/10.0)
            if value_change != 0.0:
                self.value_changed = True
            self.set_value(self.original_value + value_change)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        if not self.value_changed:
            self.label.setPos(3+5,15-5)
            self.label.set_text_interaction(True)
        self.value_changed = False

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
