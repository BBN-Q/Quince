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
import ctypes

from quince.view import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, nargs='?', help='Measurement library filename', default=None)

    args = parser.parse_args()

    app = QApplication([])
    
    # Setup icon
    png_path = os.path.join(os.path.dirname(__file__), "assets/quince_icon.png")
    app.setWindowIcon(QIcon(png_path))

    # Convince windows that this is a separate application to get the task bar icon working
    # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    if (os.name == 'nt'):
        myappid = u'BBN.quince.gui.0001' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = NodeWindow()
    if args.filename:
        window.load_yaml(args.filename)
    elif os.getenv('BBN_MEAS_FILE'):
        window.load_yaml(os.getenv('BBN_MEAS_FILE'))
    else:
        print("No filename supplied, and could not locate BBN_MEAS_FILE environment variable.")
        window.load_yaml(None)
    app.aboutToQuit.connect(window.cleanup)
    window.show()

    sys.exit(app.exec_())
