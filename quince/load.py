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

def load_from_pyqlab(graphics_view):

    name_changes = {'KernelIntegration': 'KernelIntegrator',
                    'DigitalDemod': 'Channelizer'}

    with open(graphics_view.window.measFile, 'r') as FID:
        settings = json.load(FID)
        graphics_view.meas_settings = settings["filterDict"]
        graphics_view.meas_settings_version = settings["version"]

    with open(graphics_view.window.instrFile, 'r') as FID:
        settings = json.load(FID)
        graphics_view.instr_settings = settings["instrDict"]
        graphics_view.instr_settings_version = settings["version"]

    with open(graphics_view.window.sweepFile, 'r') as FID:
        graphics_view.sweep_settings = json.load(FID)["sweepDict"]

    loaded_measure_nodes = {} # Keep track of nodes we create
    loaded_instr_nodes = {} # Keep track of nodes we create
    new_wires = []

    # Create and place the filters
    for meas_par in graphics_view.meas_settings.values():

        meas_name = meas_par["label"]
        meas_type = meas_par["x__class__"]
        # Perform some translation
        if meas_type in name_changes.keys():
            meas_type = name_changes[meas_type]
        # See if the filter exists, and then create it
        if hasattr(graphics_view, 'create_'+meas_type):
            new_node = getattr(graphics_view, 'create_'+meas_type)()
            new_node.enabled = meas_par['enabled']

            # Set the parameters:
            new_node.base_params = {}
            for k, v in meas_par.items():
                if k in new_node.parameters.keys():
                    new_node.parameters[k].set_value(v)
                else:
                    new_node.base_params[k] = v

            new_node.setOpacity(0.0)
            stored_loc = graphics_view.settings.value("node_positions/" + meas_name + "_pos")
            if stored_loc is not None and isinstance(stored_loc, QPointF):
                new_node.setPos(stored_loc)
            else:
                new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
            new_node.label.setPlainText(meas_name)
            loaded_measure_nodes[meas_name] = new_node

    # Create and place the instruments
    for instr_par in graphics_view.instr_settings.values():
        instr_name = instr_par["label"]
        instr_type = instr_par["x__class__"]
        # Perform some translation
        if instr_type in name_changes.keys():
            instr_type = name_changes[instr_type]
        # See if the filter exists, and then create it
        if hasattr(graphics_view, 'create_'+instr_type):
            new_node = getattr(graphics_view, 'create_'+instr_type)()
            new_node.enabled = instr_par['enabled']
            new_node.base_params = instr_par
            new_node.setOpacity(0.0)
            stored_loc = graphics_view.settings.value("node_positions/" + instr_name + "_pos")
            if stored_loc is not None:
                new_node.setPos(stored_loc)
            else:
                new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
            new_node.label.setPlainText(instr_name)
            loaded_instr_nodes[instr_name] = new_node

    for name, node in loaded_measure_nodes.items():
        meas_name = graphics_view.meas_settings[name]["label"]

        # Get the source name. If it contains a colon, then the part before the colon
        # is the node name and the part after is the connector name. Otherwise, the
        # connector name is just "source" and the source name is the node name.

        source = graphics_view.meas_settings[name]["data_source"].split(":")
        node_name = source[0]
        conn_name = "source"
        if len(source) == 2:
            conn_name = source[1]

        if node_name in loaded_measure_nodes.keys():
            start_node = loaded_measure_nodes[node_name]
            if conn_name in start_node.outputs.keys():
                if 'sink' in node.inputs.keys():
                    # Create wire and register with scene
                    new_wire = Wire(start_node.outputs[conn_name])
                    new_wire.setOpacity(0.0)
                    new_wires.append(new_wire)
                    graphics_view.addItem(new_wire)

                    # Add to start node
                    new_wire.set_start(start_node.outputs[conn_name].scenePos())
                    start_node.outputs[conn_name].wires_out.append(new_wire)

                    # Add to end node
                    new_wire.end_obj = node.inputs['sink']
                    new_wire.set_end(node.inputs['sink'].scenePos())
                    node.inputs['sink'].wires_in.append(new_wire)
                else:
                    print("Could not find sink connector in", meas_name)
            else:
                print("Could not find source connector ", conn_name, "for node", node_name)

        elif node_name in loaded_instr_nodes.keys():
            start_node = loaded_instr_nodes[node_name]
            if conn_name in start_node.outputs.keys():
                if 'sink' in node.inputs.keys():
                    # Create wire and register with scene
                    new_wire = Wire(start_node.outputs[conn_name])
                    new_wire.setOpacity(0.0)
                    new_wires.append(new_wire)
                    graphics_view.addItem(new_wire)

                    # Add to start node
                    new_wire.set_start(start_node.outputs[conn_name].scenePos())
                    start_node.outputs[conn_name].wires_out.append(new_wire)

                    # Add to end node
                    new_wire.end_obj = node.inputs['sink']
                    new_wire.set_end(node.inputs['sink'].scenePos())
                    node.inputs['sink'].wires_in.append(new_wire)
                else:
                    print("Could not find sink connector ", conn_name)
        else:
            print("Could not find data_source")

        graphics_view.anim_group = QParallelAnimationGroup()
        for item in new_wires + list(loaded_instr_nodes.values()) + list(loaded_measure_nodes.values()):
            dummy = dummy_object_float(item.opacity, item.setOpacity)
            anim = QPropertyAnimation(dummy, bytes("dummy".encode("ascii")))
            anim.setDuration(300)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            graphics_view.anim_group.addAnimation(anim)

        graphics_view.anim_group.start()

        # graphics_view.fade_in_items()

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


def parse_quince_module(mod_name, mod, base_class, graphics_view, x__module__, submenu=None, mod_filter=None):
    new_objects = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f)
                                                            and issubclass(f, base_class)
                                                            and f != base_class}

    if mod_filter:
        new_objects = {n: f for n, f in new_objects.items() if mod_filter(f)}

    if len(new_objects) > 0:
        if submenu:
            sm = submenu.addMenu(mod_name)
        else:
            sm = graphics_view.menu.addMenu(mod_name)
        graphics_view.sub_menus[mod_name] = sm

    # These haven't been instantiated, so the input and output
    # connectors should be a simple list in the class dictionary
    for obj_name in sorted(new_objects.keys()):
        obj = new_objects[obj_name]

        # Create a QAction and add to the menu
        action = QAction(obj_name, graphics_view)

        # Create function for dropping node on canvas
        def create(the_obj, the_name, the_category):
            node = Node(the_name, graphics_view)
            node.cat_name = the_category
            obj_instance = the_obj()

            if isinstance(obj_instance, Filter):
                # Add connectors based on the Filter's stated inputs and outputs
                for op in obj_instance._output_connectors:
                    conn = Connector(op, 'output')
                    conn.auspex_object = obj_instance.output_connectors[op]
                    node.add_output(conn)
                for ip in obj_instance._input_connectors:
                    conn = Connector(ip, 'input')
                    conn.auspex_object = obj_instance.input_connectors[ip]
                    node.add_input(conn)
                for auspex_param in obj_instance.quince_parameters:
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
                    if hasattr(auspex_param, 'default') and auspex_param.default:
                        quince_param.set_value(auspex_param.default)

                    quince_param.has_input = False
                    quince_param.auspex_object = auspex_param
                    node.add_parameter(quince_param)
            elif isinstance(obj_instance, Instrument):
                # Add a single output connector for any digitizers
                node.add_output(Connector('source', 'output'))

            # Set the class and module infor for PyQLab
            node.auspex_object = obj_instance
            node.x__class__    = the_name
            node.x__module__   = x__module__

            # See if names will be duplicated
            node_names = [i.label.toPlainText() for i in graphics_view.items() if isinstance(i, Node)]
            nan = next_available_name(node_names, the_name)
            node.label.setPlainText(nan)

            node.setPos(graphics_view.backdrop.mapFromParent(graphics_view.last_click))
            node.setPos(graphics_view.last_click)
            graphics_view.addItem(node)
            return node

        # Add to class
        name = "create_"+("".join(obj_name.split()))
        setattr(graphics_view, name, partial(create, obj, obj_name, mod_name))
        func = getattr(graphics_view, name)

        # Connect trigger for action
        create_command = lambda: graphics_view.undo_stack.push(CommandAddNode(name, func, graphics_view))
        action.triggered.connect(create_command)
        graphics_view.sub_menus[mod_name].addAction(action)

def parse_quince_modules(graphics_view):
    # Find all of the filters
    filter_modules = {
        name: importlib.import_module('auspex.filters.' + name)
        for loader, name, is_pkg in pkgutil.iter_modules(auspex_filt.__path__)
    }
    filter_modules.pop('filter') # We don't want the base class

    # Find all of the instruments
    instrument_modules = {
        name: importlib.import_module('auspex.instruments.' + name)
        for loader, name, is_pkg in pkgutil.iter_modules(instr.__path__)
    }

    for mod_name in sorted(filter_modules.keys(), key=lambda s: s.lower()):
        mod = filter_modules[mod_name]
        parse_quince_module(mod_name, mod, Filter, graphics_view, "MeasFilters")

    graphics_view.menu.addSeparator()
    graphics_view.instruments_menu = graphics_view.menu.addMenu("instruments")
    graphics_view.sub_menus["instruments"] = graphics_view.instruments_menu

    for mod_name in sorted(instrument_modules.keys(), key=lambda s: s.lower()):
        mod = instrument_modules[mod_name]
        parse_quince_module(mod_name, mod, Instrument, graphics_view, "instruments.Digitizers",
                            submenu=graphics_view.instruments_menu,
                            mod_filter=lambda m: hasattr(m, 'instrument_type') and m.instrument_type == "Digitizer")
