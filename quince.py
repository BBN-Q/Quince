# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file runs the main loop

from PyQt5.QtWidgets import QApplication
import sys

from quince.view import *

if __name__ == "__main__":

    app = QApplication([])
    window = NodeWindow()
    app.aboutToQuit.connect(window.cleanup)
    window.show()

    sys.exit(app.exec_())