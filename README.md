![quince-small](doc/images/quince-small.png)
[![Documentation Status](https://readthedocs.org/projects/quince/badge/?version=latest)](http://quince.readthedocs.io/en/latest/?badge=latest)

This project is intended as an alternative means of defining the topology of an experiment, and will augment certain functionality of PyQLab's ExpSettingsGUI. Currently envisioned use cases:

1. Graphically construct measurement filter pipelines.
2. Graphically establish logical qubits with physical measurement apparatus.

Full documentation can be found at [readthedocs](http://quince.readthedocs.io/en/latest/)

## Dependencies ##

Python Packages
1. Python 3
1. PyQt5
1. networkx
1. JSONLibraryUtils

### Linux ###

PyQT5 needs to know where to find the platform plugins.  On Anaconda Linux install this does not seem to work without explicitly pointing it to the plugin path:
```shell
QT_QPA_PLATFORM_PLUGIN_PATH=/home/cryan/anaconda3/lib/qt5/plugins/ && python quince.py
```
