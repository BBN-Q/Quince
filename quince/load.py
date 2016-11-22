# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains procedures for loading nodes
# directly from auspex as well as from file

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtSvg import *
from qtpy.QtWidgets import *

from .node import *

import os
import json
from functools import partial

def parse_node_file(filename, graphics_view):
    with open(filename) as data_file:
        cat  = os.path.basename(os.path.dirname(filename))
        data = json.load(data_file)

        # Create a QAction and add to the menu
        action = QAction(data['name'], graphics_view)

        # Create function for dropping node on canvas
        def create(the_data, cat_name):
            node = Node(the_data['name'], graphics_view)
            node.cat_name = cat_name
            for op in the_data['outputs']:
                node.add_output(Connector(op, 'output'))
            for ip in the_data['inputs']:
                node.add_input(Connector(ip, 'input'))
            for p in the_data['parameters']:
                if p['type'] == 'str':
                    pp = StringParameter(p['name'])
                elif p['type'] == 'filename':
                    pp = FilenameParameter(p['name'])
                elif p['type'] == 'float':
                    pp = NumericalParameter(p['name'], float, p['low'], p['high'], p['increment'], p['snap'])
                elif p['type'] == 'int':
                    pp = NumericalParameter(p['name'], int, p['low'], p['high'], p['increment'], p['snap'])
                elif p['type'] == 'combo':
                    pp = ComboParameter(p['name'], p['choices'])
                elif p['type'] == 'boolean':
                    pp = BooleanParameter(p['name'])

                if 'default' in p.keys():
                    pp.set_value(p['default'])

                pp.has_input = False

                # # Generally, combo, bool, file parameters have no input connectors
                # if p['type'] in ['combo', 'boolean', 'filename']:
                #     pp.has_input = False

                # # If the has_input value is set in the json, pay attention
                # if 'has_input' in p.keys():
                #     pp.has_input = p['has_input']

                # Special parameters cannot be directly edited
                if 'interactive' in p.keys():
                    pp.set_interactive(p['interactive'])

                node.add_parameter(pp)

            # Connector constraints
            if 'allowed_destinations' in the_data.keys():
                node.allowed_destinations = the_data['allowed_destinations']

            # Set the class and module infor for PyQLab
            node.x__class__  = the_data['x__class__']
            node.x__module__ = the_data['x__module__']

            # Custom coloring
            if cat_name == "Inputs":
                node.set_title_color(QColor(80,100,70))
            elif cat_name == "Outputs":
                node.set_title_color(QColor(120,70,70))
            # See if names will be duplicated
            node_names = [i.label.toPlainText() for i in graphics_view.items() if isinstance(i, Node)]
            nan = next_available_name(node_names, the_data['name'])
            node.label.setPlainText(nan)

            node.setPos(graphics_view.backdrop.mapFromParent(graphics_view.last_click))
            node.setPos(graphics_view.last_click)
            graphics_view.addItem(node)
            return node

        # Add to class
        name = "create_"+("".join(data['name'].split()))
        setattr(graphics_view, name, partial(create, data, cat))
        func = getattr(graphics_view, name)

        # Connect trigger for action
        create_command = lambda: graphics_view.undo_stack.push(CommandAddNode(name, func, graphics_view))
        action.triggered.connect(create_command)
        graphics_view.sub_menus[cat].addAction(action)