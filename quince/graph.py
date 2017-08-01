# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains the implementation of graph algorithms with network

import networkx as nx

try:
    import auspex.globals
    auspex.globals.auspex_dummy_mode = True
    from auspex.experiment import Experiment
    from auspex.stream import DataStream, DataAxis, SweepAxis, DataStreamDescriptor, OutputConnector
except ImportError as e:
    print("Could not load Auspex because or error '{}'".format(str(e)))

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

def graph_input_nodes(graph):
    return [n for n in graph.nodes() if graph.in_degree(n) == 0]

def create_experiment_graph(nodes, wires):
    exp = Experiment()

    # Add output connectors to the experiment
    for node in nodes:
        if hasattr(node.auspex_object, 'instrument_type') and node.auspex_object.instrument_type == "Digitizer":
            name = node.label.toPlainText()
            conn = OutputConnector(name=name, data_name=name, parent=exp)
            exp.output_connectors[name] = conn
            setattr(exp, name, conn)
            node.outputs["source"].auspex_object = conn

    graph = []
    for wire in wires:
        graph.append((wire.start_obj.auspex_object, wire.end_obj.auspex_object))
    exp.set_graph(graph)

    print(exp)
    return exp

def hierarchy_pos(G, root, width=600., vert_gap = 175, vert_loc = 0, xcenter = 0.0, 
                  pos = None, parent = None):
    '''from: http://stackoverflow.com/questions/29586520/can-one-get-hierarchical-graphs-from-networkx-with-python-3
       If there is a cycle that is reachable from root, then this will see infinite recursion.
       G: the graph
       root: the root node of current branch
       width: horizontal space allocated for this branch - avoids overlap with other branches
       vert_gap: gap between levels of hierarchy
       vert_loc: vertical location of root
       xcenter: horizontal location of root
       pos: a dict saying where all nodes go if they have been assigned
       parent: parent of this branch.'''
    if pos == None:
        pos = {root:(xcenter,vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)
    neighbors = G.neighbors(root)
    if len(neighbors)!=0:
        dx = width/len(neighbors) 
        nextx = xcenter - width/2 - dx/2
        for neighbor in neighbors:
            nextx += dx
            pos = hierarchy_pos(G,neighbor, width = dx, vert_gap = vert_gap, 
                                vert_loc = vert_loc-vert_gap, xcenter=nextx, pos=pos, 
                                parent = root)
    return pos

