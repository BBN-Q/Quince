![quince-small](/uploads/931ad19ca639cd00291924809fb784d5/quince-small.png)

This project is intended as an alternative means of defining the topology of an experiment, and will replace certain functionality of ExpSettingsGUI. Currently envisioned use cases:

1. Graphically construct measurement filter pipelines.
2. Graphically establish logical qubits with physical measurement apparatus.

## General Outline ##

1. Measurement topology is established by dragging wires between nodes.
2. Each node is described by a single JSON file.
3. Node parameters (e.g. frequency on a signal generator) are set manually or associated with sweeps.
4. The graphs are saved to JSON format describing the nodes (with parameters), and wires between them.

## Requirements ##

Python Packages
1. PyQt5
2. networkx (maybe)