# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the sweep/parameter inspector descriptions

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class NodeListView(QListView):
    """List view with a node-centric model. Probably we'll 
    be doing some more custom work here, later."""
    def __init__(self, parent=None):
        super(NodeListView, self).__init__(parent=parent)
        self.parent = parent
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.setDragDropMode(QListView.InternalMove)
