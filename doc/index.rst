.. Quince documentation master file, created by
   sphinx-quickstart on Fri Oct 21 14:40:35 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: images/quince-small.png
   :width: 256 px
   :align: center


Introduction
************

Quince allows users to graphically create and manipulate nodes, and integrates
with *PyQLab* and *Auspex* in order that it can be used to define the filter
pipeline for experiments.

Installation & Requirements
***************************

Quince requires:

- Python 3
- PyQt5
- networkx
- ruamel.yaml >= 0.15.18
- Auspex 

We recommend using an anaconda installation on windows, while there are a
variety of viable approaches on Linux/MacOS. Quince can be cloned from GitHub::

	git clone https://github.com/BBN-Q/Quince.git

Then you may install Quince via pip::

	cd Quince
	pip install -e .
	./run-quince.py

Populating the Node Menus
*************************

Quince automatically generates its nodes by walking the auspex modules. To perform this
function, Auspex must be on the python path. 


Contents:

.. toctree::
   :maxdepth: 2
