.. Quince documentation master file, created by
   sphinx-quickstart on Fri Oct 21 14:40:35 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: images/quince-small.png
   :width: 256 px
   :align: center


Introduction
************

Quince allows users to graphically create and manipulate nodes, and integrates with *PyQLab* and *Auspex* in order that it can be used to define the filter pipeline for experiments.

Installation & Requirements
***************************

Quince requires:

- Python 3
- PyQt5
- networkx
- JSONLibraryUtils

We recommend using an anaconda installation on windows, while there are a variety of viable approaches on Linux/MacOS. Quince can be cloned from GitHub::

	git clone https://github.com/BBN-Q/Quince.git

If you plan to use Quince in consort with PyQLab, and are using anaconda on Windows, there be conflicts in PyQt versions since PyQLab requires PyQt4. In this case, we recommend creating a new virtual environment for PyQt5::
	
	conda create -n pyqt5 python

On windows, *setup.py* automatically creates a *run-quince.bat* script that will launch the correct python environment (assuming it is named "pyqt5") and start quince. You will need to move this script somewhere that is on your system path (since your environment scripts directory will not be on the path). To summarize, after creating your environment, run::

	activate pyqt5
	cd Quince
	pip install -e .
	copy run-quince.bat SOMEWHERE_ON_MY_PATH
	run-quince.bat

On Linux or mac, the interpreter should be chosen automatically, so one need only run::

	cd Quince
	pip install -e .
	run-quince.py 

Populating the Node Menus
*************************

Quince generates its menus by parsin json node description files. To automatically generate these files for *Auspex* filters, ensure that *Auspex* is on the path and then run::

	./find_filters.py

to create and populate the auspex-nodes folder.


Contents:

.. toctree::
   :maxdepth: 2
