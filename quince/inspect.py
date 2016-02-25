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

class SweepLayout(QFormLayout):
    def __init__(self, sweep_node, parent=None):
        super(SweepLayout, self).__init__(parent=parent)
        self.parent = parent

        # Change inputs depending on datatype
        input_type_map = {float: QDoubleSpinBox, int: QSpinBox}

        wires_out = sweep_node.outputs['Swept Param.'].wires_out
        if len(wires_out) == 0:
            print("This sweep is not hooked up to anything.")
            datatype = int
            connected_parameter = None
        else:
            connected_parameter = sweep_node.outputs['Swept Param.'].wires_out[0].end_obj
            print(connected_parameter.name)
            datatype = connected_parameter.datatype

        self.start     = input_type_map[datatype]()
        self.stop      = input_type_map[datatype]()
        self.increment = input_type_map[datatype]()
        self.steps     = QSpinBox()

        self.addRow("Start", self.start)
        self.addRow("Stop", self.stop)
        self.addRow("Increment", self.increment)
        self.addRow("Steps", self.steps)

