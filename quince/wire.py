# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the wire descriptions

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *

from .conn import *
from .param import *

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
        self.end_image.setBrush(QColor(130, 170, 170))
        self.end_image.setPos(self.start)

        # Setup behavior for unlinking the end of the wire, monkeypatch!
        def mpe(event):
            self.unhook(event)
        def mme(event):
            self.set_end(event.scenePos())
            exclude = list(self.start_obj.parent.inputs.values())
            self.scene().connectors_nearby(event.scenePos(), exclude=exclude)
        def mre(event):
            exclude = list(self.start_obj.parent.inputs.values())
            nearest = self.scene().connectors_nearby(event.scenePos(), exclude=exclude)
            self.decide_drop(nearest)

        self.end_image.mousePressEvent   = mpe
        self.end_image.mouseMoveEvent    = mme
        self.end_image.mouseReleaseEvent = mre

    def unhook(self, event):
        self.end_obj.wires_in.remove(self)
        self.start_obj.wires_out.remove(self)
        self.end_obj = None

    def decide_drop(self, drop_site):
        self.setVisible(False)
        success = True

        if isinstance(drop_site, Connector):
            if self.start_obj.parent.name in ["Sweep", "Parameter"]:
                self.scene().window.set_status("Can't connect a sweep or parameter to a data connector.")
            elif drop_site.connector_type == 'input':

                # Check if there are restrictions on the allowed drop destinations, then act on them
                if len(self.start_obj.parent.allowed_destinations) > 0 and self.start_obj.name in self.start_obj.parent.allowed_destinations.keys():
                    success = drop_site.name == self.start_obj.parent.allowed_destinations[self.start_obj.name]
                    if not success:
                        self.scene().window.set_status("Can't connect {} connector to {}, only to {}.".format(self.start_obj.name, drop_site.name, self.start_obj.parent.allowed_destinations[self.start_obj.name]))

        elif isinstance(drop_site, Parameter):
            if self.start_obj.parent.name in ["Sweep", "Parameter"]:
                
                # Update the datatypes for sweep objects
                if self.start_obj.parent.name == "Sweep":
                    self.start_obj.parent.update_fields_from_connector()
            else:
                self.scene().window.set_status("Can't connect data connector to parameter.")
                success = False

        else:
            success = False

        if success:
            self.set_end(drop_site.scenePos())
            self.end_obj = drop_site
            self.end_obj.setRect(-5.0, -5.0, 10, 10)
            self.end_obj.wires_in.append(self)
            self.start_obj.wires_out.append(self)
            self.make_path()

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
        self.path.moveTo(self.start.x()+7, self.start.y())
        halfway_x = self.start.x() + 0.5*(self.end.x()-self.start.x())
        self.path.cubicTo(halfway_x, self.start.y(), halfway_x, self.end.y(), self.end.x(), self.end.y())
        self.setPath(self.path)
        self.setBrush(QBrush(Qt.NoBrush))

        linear_gradient = QLinearGradient(self.start, self.end)
        linear_gradient.setColorAt(0, QColor(128, 128, 128))
        if self.end_obj:
            linear_gradient.setColorAt(1.0, QColor(180, 220, 220))
            line_type = Qt.SolidLine
        else:
            linear_gradient.setColorAt(1.0, QColor(220, 220, 180))
            line_type = Qt.DashLine
        
        self.setPen(QPen(QBrush(linear_gradient), 4.0, line_type, Qt.RoundCap))


    def dict_repr(self):
        dat = {}
        dat['start'] = {'node': self.start_obj.parent.label.toPlainText(), 'connector_name': self.start_obj.name}
        dat['end'] = {'node': self.end_obj.parent.label.toPlainText(), 'connector_name': self.end_obj.name}
        return dat
