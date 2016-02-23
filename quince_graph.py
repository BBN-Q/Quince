# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the implementation of graph algorithms with network

import networkx as nx

def generate_graph(wires):
	edges = [(w.start_obj.parent.label.toPlainText(), w.end_obj.parent.label.toPlainText()) for w in wires]
	graph = nx.Graph()
	graph.add_edges_from(edges)
	return graph

def items_on_subgraph(graph, node):
	sub_graphs = nx.connected_component_subgraphs(graph)
	for sg in sub_graphs:
		if node in sg.nodes():
			return sg
	return []