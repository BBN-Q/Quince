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

import os, os.path
import json
import importlib
import pkgutil
import inspect
import sys
from functools import partial

try:
    import auspex
    import auspex.filters as auspex_filt
    import auspex.instruments as instr
    from auspex.filters.filter import Filter
    import auspex.parameter
    from auspex.instruments.instrument import Instrument, SCPIInstrument, CLibInstrument
except:
    no_auspex = True
    print("Could not locate auspex in the python path. Will only load json nodes.")

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

def parse_quince_modules(graphics_view):
    # Find all of the filters
    filter_modules = {
        name: importlib.import_module('auspex.filters.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(auspex_filt.__path__)
    }
    filter_modules.pop('filter') # We don't want the base class

    # Find all of the instruments
    instrument_vendors = {
        name: importlib.import_module('auspex.instruments.' + name)
        for loader, name, is_pkg in pkgutil.iter_modules(instr.__path__)
    }
            
    for mod_name in sorted(filter_modules.keys(), key=lambda s: s.lower()):
        mod = filter_modules[mod_name]

        new_filters = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f)
                                                                and issubclass(f, Filter)
                                                                and f != Filter}
        if len(new_filters) > 0:
            sm = graphics_view.menu.addMenu(mod_name)
            graphics_view.sub_menus[mod_name] = sm

        # These haven't been instantiated, so the input and output
        # connectors should be a simple list in the class dictionary
        for filt_name in sorted(new_filters.keys()):
            filt = new_filters[filt_name]

            # Create a QAction and add to the menu
            action = QAction(filt_name, graphics_view)

            # Create function for dropping node on canvas
            def create(the_filter, the_name, the_category):
                node = Node(the_name, graphics_view)
                node.cat_name = the_category
                for op in the_filter._output_connectors:
                    node.add_output(Connector(op, 'output'))
                for ip in the_filter._input_connectors:
                    node.add_input(Connector(ip, 'input'))

                filter_instance = the_filter()
                for auspex_param in filter_instance.quince_parameters:
                    if isinstance(auspex_param, auspex.parameter.FloatParameter) or isinstance(auspex_param, auspex.parameter.IntParameter):
                        if auspex_param.value_range:
                            low  = min(auspex_param.value_range)
                            high = max(auspex_param.value_range)
                        else:
                            low = -1e15
                            high = 1e15
                            auspex_param.increment = 2e14

                        if not auspex_param.increment:
                            auspex_param.increment = 0.05*(high-low)
                        
                        snap = auspex_param.snap
                    
                    if isinstance(auspex_param, auspex.parameter.FloatParameter):
                        quince_param = NumericalParameter(auspex_param.name, float,
                                        low, high, auspex_param.increment, auspex_param.snap)
                    elif isinstance(auspex_param, auspex.parameter.IntParameter):
                        quince_param = NumericalParameter(auspex_param.name, int,
                                        low, high, auspex_param.increment, auspex_param.snap)
                    elif isinstance(auspex_param, auspex.parameter.BoolParameter):
                        quince_param = BooleanParameter(auspex_param.name)
                    elif isinstance(auspex_param, auspex.parameter.FilenameParameter):
                        quince_param = FilenameParameter(auspex_param.name)
                    elif isinstance(auspex_param, auspex.parameter.Parameter):
                        if auspex_param.allowed_values:
                            quince_param = ComboParameter(auspex_param.name, auspex_param.allowed_values)
                        else:
                            quince_param = StringParameter(auspex_param.name) 
                    if auspex_param.default:
                        quince_param.set_value(auspex_param.default)

                    quince_param.auspex_object = auspex_param
                    node.add_parameter(quince_param)

                # Set the class and module infor for PyQLab
                node.auspex_object = filter_instance
                node.x__class__    = the_name
                node.x__module__   = "MeasFilters"

                # See if names will be duplicated
                node_names = [i.label.toPlainText() for i in graphics_view.items() if isinstance(i, Node)]
                nan = next_available_name(node_names, the_name)
                node.label.setPlainText(nan)

                node.setPos(graphics_view.backdrop.mapFromParent(graphics_view.last_click))
                node.setPos(graphics_view.last_click)
                graphics_view.addItem(node)
                return node

            # Add to class
            name = "create_"+("".join(filt_name.split()))
            setattr(graphics_view, name, partial(create, filt, filt_name, mod_name))
            func = getattr(graphics_view, name)

            # Connect trigger for action
            create_command = lambda: graphics_view.undo_stack.push(CommandAddNode(name, func, graphics_view))
            action.triggered.connect(create_command)
            graphics_view.sub_menus[mod_name].addAction(action)

