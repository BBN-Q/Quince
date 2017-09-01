![quince-small](doc/images/quince-small.png)
[![Documentation Status](https://readthedocs.org/projects/quince/badge/?version=latest)](http://quince.readthedocs.io/en/latest/?badge=latest)

This project is intended as an alternative means of defining the topology of an experiment, and will augment certain functionality of [PyQLab's](https://github.com/BBN-Q/PyQLab) ExpSettingsGUI. Currently envisioned use cases:

1. Graphically construct measurement filter pipelines.
2. Graphically establish logical qubits with physical measurement apparatus.

Full documentation can be found at [Read the Docs](http://quince.readthedocs.io/en/latest/)

## Dependencies

1. Python 3
2. [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)
3. [QtPy](https://github.com/spyder-ide/qtpy)
4. [networkx](https://networkx.github.io/)
5. [ruamel.yaml](https://pypi.python.org/pypi/ruamel.yaml)
6. [Auspex](https://github.com/BBN-Q/auspex) - necessary for populating filter and instrument nodes

## Funding

This software is based in part upon work supported by the Office of the Director of National Intelligence (ODNI), Intelligence Advanced Research Projects Activity (IARPA), via contract W911NF-14-C0089 and Army Research Office contract No. W911NF-14-1-0114. The views and conclusions contained herein are those of the authors and should not be interpreted as necessarily representing the official policies or endorsements, either expressed or implied, of the ODNI, IARPA, or the U.S. Government.
