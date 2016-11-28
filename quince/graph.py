# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the implementation of graph algorithms with network

import networkx as nx

try:
    from auspex.experiment import Experiment
    from auspex.stream import DataStream, DataAxis, SweepAxis, DataStreamDescriptor, OutputConnector
except:
    print("Cause not load Auspex")

def generate_graph(wires, dag=False):
    edges = [(w.start_obj.parent.label.toPlainText(), w.end_obj.parent.label.toPlainText()) for w in wires]
    if dag:
        graph = nx.DiGraph()
    else:
        graph = nx.Graph()
    graph.add_edges_from(edges)
    return graph

def items_on_subgraph(graph, node):
    sub_graphs = nx.connected_component_subgraphs(graph)
    for sg in sub_graphs:
        if node in sg.nodes():
            return sg
    return []

def descendants(graph, node):
    return nx.descendants(graph, node)

def create_experiment_graph(nodes, wires):
    exp = Experiment()

    for node in nodes:
        if node.auspex_object.instrument_type == "Digitizer":
            conn = OutputConnector(name=oc, data_name=oc, parent=self)
            conn.parent = exp
            exp.output_connectors[oc] = conn
            setattr(exp, oc, conn)

    graph = []
    for wire in wires:
        graph.append((wire.start_obj.auspex_object, wire.end_obj.auspex_object))
    exp.set_graph(graph)

    print(exp)
    return exp