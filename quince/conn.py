# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the connector descriptions

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *

class Connector(QGraphicsEllipseItem):
    """docstring for Connector"""
    def __init__(self, name, connector_type, parent=None):
        rad = 5
        super(Connector, self).__init__(-rad, -rad, 2*rad, 2*rad, parent=parent)
        self.name = name
        self.parent = parent
        self.connector_type = connector_type
        self.setZValue(1)

        self.temp_wire = None
        self.wires_in  = []
        self.wires_out = []

        # Text label and area
        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.black)

        if self.connector_type == 'output':
            self.label.setPos(-5-self.label.boundingRect().topRight().x(),-10)      
            self.setBrush(Qt.white)
            self.setPen(QColor(50,50,50))
        else:
            self.label.setPos(5,-10)      
            self.setBrush(Qt.white)
            self.setPen(QColor(50,50,50))

    def width(self):
        return self.label.boundingRect().topRight().x()

    def height(self):
        return 15

    def mousePressEvent(self, event):
        self.temp_wire = self.parent.create_wire(self) # Avoid circular imports
        self.scene().addItem(self.temp_wire)

    def mouseMoveEvent(self, event):
        if self.temp_wire is not None:
            self.temp_wire.set_end(event.scenePos())

    def mouseReleaseEvent(self, event):
        self.temp_wire.decide_drop(event)
        self.scene().clear_wires(only_clear_orphaned=True)
