# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the implementation of graph algorithms with network

import networkx as nx

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
