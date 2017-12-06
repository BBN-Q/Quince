# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the connector descriptions

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from .util import *
import numpy as np

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

        # Associate with auspex connectors
        self.auspex_object = None

        # self.timeline = QTimeLine()
        self.wire_anim_group = QParallelAnimationGroup()
        self.exploded = False
        self.wires_to_anims = {}

    def explode_wires(self):
        if not self.exploded and self.wire_anim_group.state() == QAbstractAnimation.Stopped:
            self.wires_to_anims = {}
            self.wire_anim_group.clear()
            self.wire_anim_group.setDirection(QAbstractAnimation.Forward)
            wires = sorted([w for w in self.wires_in if w.end_obj is not None], key=lambda c: c.start_obj.parent.y())
            start = np.pi/6.0
            norm_fac = (np.pi-2*start)/(len(wires)-1)
            for j, wire in enumerate(wires):
                rad = 18 #5 + 5*len(wires)
                offset = QPointF(-rad*np.sin(start + j*norm_fac), -rad*np.cos(start + j*norm_fac))
                wire_dummy = dummy_object_QPointF(wire.end_image.pos, wire.set_end)
                anim = QPropertyAnimation(wire_dummy, bytes("dummy".encode("ascii")))
                anim.setEasingCurve(QEasingCurve.OutQuad)
                anim.setDuration(150)
                anim.setStartValue(self.scenePos())
                anim.setEndValue(self.scenePos() + offset)
                self.wire_anim_group.addAnimation(anim)
                self.wires_to_anims[wire] = anim
            self.wire_anim_group.start()
            self.exploded = True
        if not self.exploded and self.wire_anim_group.state() == QAbstractAnimation.Running:
            self.wire_anim_group.pause()
            self.wire_anim_group.setDirection(QAbstractAnimation.Forward)
            self.wire_anim_group.resume()

    def implode_wires(self):
        for wire in self.wires_to_anims.copy().keys():
            if wire not in self.wires_in:
                if not wire.end_obj:
                    self.wire_anim_group.removeAnimation(self.wires_to_anims[wire])
                    self.wires_to_anims.pop(wire)

        if self.exploded and self.wire_anim_group.state() == QAbstractAnimation.Stopped:
            self.wire_anim_group.setDirection(QAbstractAnimation.Backward)
            self.wire_anim_group.start()
            # self.exploded = False
        elif self.exploded and self.wire_anim_group.state() == QAbstractAnimation.Running:
            self.wire_anim_group.pause()
            self.wire_anim_group.setDirection(QAbstractAnimation.Backward)
            self.wire_anim_group.resume()
        self.exploded = False

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
            exclude = list(self.parent.inputs.values())
            self.scene().connectors_nearby(event.scenePos(), exclude=exclude)

    def mouseReleaseEvent(self, event):
        exclude = list(self.parent.inputs.values())
        nearest = self.scene().connectors_nearby(event.scenePos(), exclude=exclude)
        self.temp_wire.decide_drop(nearest)

class CompositeConnector(Connector):
    def __init__(self, name, connector_type, parent=None):
        super(CompositeConnector, self).__init__(name, connector_type, parent=parent)