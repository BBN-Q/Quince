# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the sweep/parameter inspector descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from .param import *

class NodeListView(QListView):
    """List view with a node-centric model. Probably we'll 
    be doing some more custom work here, later."""
    def __init__(self, parent=None):
        super(NodeListView, self).__init__(parent=parent)
        self.parent = parent
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.setDragDropMode(QListView.InternalMove)

class SweepItem(QStandardItem):
    def __init__(self, text, sweep_object):
        super(SweepItem, self).__init__(text)
        self.sweep_object = sweep_object
        self.setCheckable(True)
        self.setDropEnabled(False)

class SweepLayout(QFormLayout):
    def __init__(self, sweep_node, sweep_object, parent=None):
        super(SweepLayout, self).__init__(parent=parent)
        self.parent = parent
        self.sweep_object = sweep_object
        self.sweep_node = sweep_node

        # Change inputs depending on datatype
        input_type_map = {float: QDoubleSpinBox, int: QSpinBox}

        wires_out = self.sweep_node.outputs['Swept Param.'].wires_out
        if len(wires_out) == 0:
            datatype = int
            connected_parameter = None
        else:
            connected_parameter = self.sweep_node.outputs['Swept Param.'].wires_out[0].end_obj
            datatype = connected_parameter.datatype

        self.start     = input_type_map[datatype]()
        self.stop      = input_type_map[datatype]()
        self.increment = input_type_map[datatype]()
        self.steps     = QSpinBox()

        self.start.setValue(self.sweep_object.start)
        self.stop.setValue(self.sweep_object.stop)
        self.increment.setValue(self.sweep_object.increment)
        self.steps.setValue(self.sweep_object.steps)

        self.start.valueChanged.connect(self.sweep_object.set_start)
        self.stop.valueChanged.connect(self.sweep_object.set_stop)
        self.increment.valueChanged.connect(self.sweep_object.set_increment)
        self.steps.valueChanged.connect(self.sweep_object.set_steps)

        self.start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.increment.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.steps.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.addRow("Start", self.start)
        self.addRow("Stop", self.stop)
        self.addRow("Increment", self.increment)
        self.addRow("Steps", self.steps)

        self.setContentsMargins(10,10,10,10)

class Sweep(object):
    """Simple sweep container"""
    def __init__(self):
        super(Sweep, self).__init__()
        self.start     = 0.0
        self.stop      = 0.0
        self.increment = 0.0
        self.steps     = 0.0

    def set_start(self, value):
        self.start = value
    def set_stop(self, value):
        self.stop = value
    def set_increment(self, value):
        self.increment = value
    def set_steps(self, value):
        self.steps = value
        