#!/usr/bin/env python3
# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file runs the main loop

# Use PyQt5 by default
import os
os.environ["QT_API"] = 'pyqt5'

from qtpy.QtWidgets import QApplication
import sys
import argparse

from quince.view import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--measFile',  type=str, help='Measurement Library File')
    parser.add_argument('-s', '--sweepFile', type=str, help='Sweep Library File')
    parser.add_argument('-i', '--instrFile', type=str, help='Instrument Library File')

    args = parser.parse_args()

    app = QApplication([])
    window = NodeWindow()
    window.load_pyqlab(measFile=args.measFile, sweepFile=args.sweepFile, instrFile=args.instrFile)
    app.aboutToQuit.connect(window.cleanup)
    window.show()

    sys.exit(app.exec_())
