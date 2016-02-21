# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the wire descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from quince_conn import *
from quince_param import *

class Wire(QGraphicsPathItem):
    """docstring for Wire"""
    def __init__(self, start_obj, parent=None):
        self.path = QPainterPath()
        super(Wire, self).__init__(self.path, parent=parent)

        self.parent    = parent
        self.start     = start_obj.scenePos()
        self.end       = self.start
        self.start_obj = start_obj
        self.end_obj   = None
        self.make_path()

        self.setZValue(0)
        self.set_start(self.start)

        # Add endpoint circle
        rad = 5
        self.end_image = QGraphicsEllipseItem(-rad, -rad, 2*rad, 2*rad, parent=self)
        self.end_image.setBrush(Qt.white)
        self.end_image.setPos(self.start)
        # self.end_image.setZValue(10)

        # Setup behavior for unlinking the end of the wire, monkeypatch!
        self.end_image.mousePressEvent = lambda e: self.unhook(e)
        self.end_image.mouseMoveEvent = lambda e: self.set_end(e.scenePos())
        self.end_image.mouseReleaseEvent = lambda e: self.decide_drop(e)

    def unhook(self, event):
        print("Unhooking")
        self.end_obj.wires_in.remove(self)
        self.start_obj.wires_out.remove(self)
        self.end_obj = None

    def decide_drop(self, event):
        self.setVisible(False)
        drop_site = self.scene().itemAt(event.scenePos(), QTransform())
        if isinstance(drop_site, Connector):
            if drop_site.connector_type == 'input':
                print("Connecting to data-flow connector")
                self.set_end(drop_site.scenePos())
                self.end_obj = drop_site
                drop_site.wires_in.append(self)
                self.start_obj.wires_out.append(self)
            else:
                print("Can't connect to output")
        elif isinstance(drop_site, Parameter):
            print("Connecting to parameter connector")
            self.set_end(drop_site.scenePos())
            self.end_obj = drop_site
            drop_site.wires_in.append(self)
            self.start_obj.wires_out.append(self)
        else:
            print("Bad drop!")

        self.setVisible(True)
        self.scene().clear_wires(only_clear_orphaned=True)

    def set_start(self, start):
        self.start = start
        self.make_path()

    def set_end(self, end):
        self.end = end
        self.make_path()
        self.end_image.setPos(end)

    def make_path(self):
        self.path = QPainterPath()
        self.path.moveTo(self.start.x()+5, self.start.y()+1)
        halfway_x = self.start.x() + 0.5*(self.end.x()-self.start.x())
        self.path.cubicTo(halfway_x, self.start.y(), halfway_x, self.end.y()+3, self.end.x(), self.end.y()+3)
        self.path.lineTo(self.end.x(), self.end.y()-3)
        self.path.cubicTo(halfway_x, self.end.y(), halfway_x, self.start.y()-3, self.start.x()+5, self.start.y()-1)
        self.path.lineTo(self.start.x()+5, self.start.y()+1)
        self.setPath(self.path)

        linearGradient = QLinearGradient(self.start, self.end)
        linearGradient.setColorAt(0, QColor(128, 128, 128))
        linearGradient.setColorAt(1.0, Qt.white)
        self.setBrush(QBrush(linearGradient))
        self.setPen(QPen(QColor(128, 128, 128), 0.25))

    def dict_repr(self):
        dat = {}
        dat['start'] = {'node': self.start_obj.parent.label.toPlainText(), 'connector_name': self.start_obj.name}
        dat['end'] = {'node': self.end_obj.parent.label.toPlainText(), 'connector_name': self.end_obj.name}
        return dat
