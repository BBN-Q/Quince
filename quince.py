# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file runs the main loop

from PyQt5.QtGui import *
import sys

from quince_view import *

if __name__ == "__main__":

    app = QApplication([])
    window = NodeWindow()
    app.aboutToQuit.connect(window.cleanup)
    window.show()

    sys.exit(app.exec_())