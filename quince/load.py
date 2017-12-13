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
import importlib
import pkgutil
import inspect
import sys
from shutil import move

try:
    import ruamel.yaml as yaml
except:
    try:
        import ruamel_yaml as yaml
    except:
        raise Exception("Could not find ruamel.yaml or ruamel_yaml")

from functools import partial

NO_AUSPEX = False
try:
    import auspex.config
    auspex.config.auspex_dummy_mode = True
    import auspex
    import auspex.filters as auspex_filt
    import auspex.instruments as instr
    from auspex.filters.filter import Filter
    import auspex.parameter
    from auspex.instruments.instrument import Instrument, SCPIInstrument, CLibInstrument
except ImportError as e:
    NO_AUSPEX = True
    print("Failed to load Auspex with error '{}'. There will be no nodes.".format(str(e)))

class Include():
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            self.data = yaml.load(f, Loader=yaml.RoundTripLoader)
    def __getitem__(self, key):
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
    def items(self):
        return self.data.items()
    def keys(self):
        return self.data.keys()
    def pop(self, key):
        if key in self.keys():
            return self.data.pop(key)
        else:
            raise KeyError("Could not find key {}".format(key))
    def write(self):
        with open(self.filename+".tmp", 'w') as fid:
            yaml.dump(self.data, fid, Dumper=yaml.RoundTripDumper)
        # Upon success
        move(self.filename+".tmp", self.filename)

class Loader(yaml.RoundTripLoader):
    def __init__(self, stream):
        try:
            self._root = os.path.split(stream.name)[0]
        except AttributeError:
            self._root = os.path.curdir
        super().__init__(stream)
        self.filenames = []

    def include(self, node):
        shortname = self.construct_scalar(node)
        filename = os.path.abspath(os.path.join(
            self._root, shortname
        ))
        self.filenames.append(filename)
        return Include(filename)

class Dumper(yaml.RoundTripDumper):
    def include(self, data):
        data.write()
        return self.represent_scalar(u'!include', data.filename)

def yaml_load(filename):
    with open(filename, 'r') as fid:
        Loader.add_constructor('!include', Loader.include)
        load = Loader(fid)
        code = load.get_single_data()
        filenames = load.filenames
        load.dispose()
    filenames.append(os.path.abspath(filename))
    return code, filenames

def yaml_dump(data, filename):
    with open(filename+".tmp", 'w') as fid:
        Dumper.add_representer(Include, Dumper.include)
        yaml.dump(data, fid, Dumper=Dumper)
    # Upon success
    move(filename+".tmp", filename)

def load_from_yaml(node_scene):

    name_changes = {'KernelIntegration': 'KernelIntegrator',
                    'DigitalDemod': 'Channelizer'}

    node_scene.settings, _        = yaml_load(node_scene.window.meas_file)
    node_scene.filter_settings    = node_scene.settings["filters"]
    node_scene.instr_settings     = node_scene.settings["instruments"]
    node_scene.composite_settings = node_scene.settings.get("composites", None)

    # Process the composite nodes and create menu items
    if node_scene.composite_settings:
        parse_composite_nodes(node_scene)

    # Keep track of nodes we create
    loaded_filter_nodes    = {}
    loaded_instr_nodes     = {} 
    loaded_composite_nodes = {}
    new_wires              = []

    # Create and place the filters
    for filt_name, filt_par in node_scene.filter_settings.items():

        filt_type = filt_par["type"]
        # Perform some translation
        if filt_type in name_changes.keys():
            filt_type = name_changes[filt_type]
        # See if the filter exists, and then create it
        if hasattr(node_scene, 'create_'+filt_type):
            new_node = getattr(node_scene, 'create_'+filt_type)()

            # Enabled unless otherwise specified
            if 'enabled' not in filt_par.keys():
                filt_par['enabled'] = True
            new_node.enabled = filt_par['enabled']

            # Set the quince parameters, and keep references to the remaining parameters
            # that cannot be set directly inside quince.
            new_node.base_params = {}
            for k, v in filt_par.items():
                if k in new_node.parameters.keys():
                    new_node.parameters[k].set_value(v)
                else:
                    new_node.base_params[k] = v

            new_node.setOpacity(0.0)
            try:
                # Sometimes the settings get gunked up...
                loc_x = node_scene.qt_settings.value("node_positions/" + filt_name + "_pos_x")
                loc_y = node_scene.qt_settings.value("node_positions/" + filt_name + "_pos_y")
                # Windows is very confused about this data type:
                loc_x = float(loc_x)
                loc_y = float(loc_y)
                new_node.setPos(QPointF(loc_x, loc_y))
            except:
                print("Error when loading node position from QSettings...")
                new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
                node_scene.qt_settings.setValue("node_positions/" + filt_name + "_pos_x", new_node.pos().x())
                node_scene.qt_settings.setValue("node_positions/" + filt_name + "_pos_y", new_node.pos().y())
            new_node.label.setPlainText(filt_name)
            loaded_filter_nodes[filt_name] = new_node

    # Create and place the instruments
    for instr_name, instr_par in node_scene.instr_settings.items():

        instr_type = instr_par["type"]

        # Put only digitizers on the graph
        if "rx_channels" not in instr_par.keys():
            continue

        # See if the filter exists, and then create it.
        # Assume filters are enabled unless otherwise noted.
        if hasattr(node_scene, 'create_'+instr_type):
            new_node = getattr(node_scene, 'create_'+instr_type)()
            new_node.enabled = instr_par['enabled'] if 'enabled' in instr_par.keys() else True
            new_node.base_params = instr_par
            new_node.setOpacity(0.0)
            
            try:
                # Sometimes the settings get gunked up...
                loc_x = node_scene.qt_settings.value("node_positions/" + instr_name + "_pos_x")
                loc_y = node_scene.qt_settings.value("node_positions/" + instr_name + "_pos_y")
                # Windows is very confused about this data type:
                loc_x = float(loc_x)
                loc_y = float(loc_y)
                new_node.setPos(QPointF(loc_x, loc_y))
            except:
                print("Error when loading node position from QSettings...", )
                new_node.setPos(np.random.random()*500-250, np.random.random()*500-250)
                node_scene.qt_settings.setValue("node_positions/" + instr_name + "_pos_x", new_node.pos().x())
                node_scene.qt_settings.setValue("node_positions/" + instr_name + "_pos_y", new_node.pos().y())
            new_node.label.setPlainText(instr_name)
            loaded_instr_nodes[instr_name] = new_node

    for filt_name, node in loaded_filter_nodes.items():
        """Get the source name. If it contains a colon, then the part before the colon
        is the node name and the part after is the connector name. Otherwise, the
        connector name is just "source" and the source name is the node name."""

        sources = [s.strip() for s in node_scene.filter_settings[filt_name]["source"].split(",")]
        for source in sources:

            source    = source.split()
            if len(source) == 0:
                continue

            node_name = source[0]
            conn_name = "source"
            if len(source) == 2:
                conn_name = source[1]

            if node_name in loaded_filter_nodes.keys():
                start_node = loaded_filter_nodes[node_name]
                if conn_name in start_node.outputs.keys():
                    if 'sink' in node.inputs.keys():
                        # Create wire and register with scene
                        new_wire = Wire(start_node.outputs[conn_name])
                        new_wire.setOpacity(0.0)
                        new_wires.append(new_wire)
                        node_scene.addItem(new_wire)

                        # Add to start node
                        new_wire.set_start(start_node.outputs[conn_name].scenePos())
                        start_node.outputs[conn_name].wires_out.append(new_wire)

                        # Add to end node
                        new_wire.end_obj = node.inputs['sink']
                        new_wire.set_end(node.inputs['sink'].scenePos())
                        node.inputs['sink'].wires_in.append(new_wire)
                    else:
                        print("Could not find sink connector in", filt_name)
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
                        node_scene.addItem(new_wire)

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
                print("Could not find source for ", filt_name, ":", node_name, conn_name)

    # Stick everything in an animation group and ramp the opacity up to 1 (fade in)
    node_scene.anim_group = QParallelAnimationGroup()
    for item in new_wires + list(loaded_instr_nodes.values()) + list(loaded_filter_nodes.values()):
        dummy = dummy_object_float(item.opacity, item.setOpacity)
        anim = QPropertyAnimation(dummy, bytes("dummy".encode("ascii")))
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        node_scene.anim_group.addAnimation(anim)
    node_scene.anim_group.start()

def parse_composite_nodes(node_scene):
    comp_settings = node_scene.composite_settings

    # Remove old composites submenu
    if hasattr(node_scene, "composites_menu"):
        node_scene.menu.removeAction(node_scene.composites_menu.menuAction())

    # Add composites submenu
    node_scene.composites_menu = node_scene.menu.addMenu("Composite Nodes")
    node_scene.sub_menus["composites"] = node_scene.composites_menu
    
    # Add special input and output connector node types
    ci_action = QAction("Composite Input", node_scene)
    co_action = QAction("Composite Output", node_scene)
    node_scene.sub_menus["composites"].addAction(ci_action)
    node_scene.sub_menus["composites"].addAction(co_action)
    node_scene.composites_menu.addSeparator()

    # Create creation functions and actions for each type
    for comp_name in sorted(comp_settings.keys()):
        comp = comp_settings[comp_name]

        # Create a QAction and add to the menu
        action = QAction(comp_name, node_scene)

        # Create function for dropping node on canvas
        def create(settings, the_name):
            node = CompositeNode(the_name, node_scene)
            node.cat_name = "composites"
            node.composite_settings = comp

            for filt_name, filt_set in settings["filters"].items():
                node.auspex_filter_objects[filt_name] = node_scene.auspex_objects[filt_set['type']]()
                node.composite_settings = settings

            # Add connectors based on the Filter's stated inputs and outputs
            for s in settings["outputs"]:
                node_name, conn_name = s.split()
                conn = CompositeConnector(conn_name, 'output')
                conn.auspex_object = node.auspex_filter_objects[node_name].output_connectors[conn_name]
                node.add_output(conn)
            for s in settings["inputs"]:
                node_name, conn_name = s.split()
                conn = CompositeConnector(conn_name, 'input')
                conn.auspex_object = node.auspex_filter_objects[node_name].input_connectors[conn_name]
                conn.auspex_object = None
                node.add_input(conn)
            for s in settings["parameters"]:
                node_name, param_name = s.split()
                auspex_param = {n.name: n for n in node.auspex_filter_objects[node_name].quince_parameters}[param_name]

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

            # Set the class and module info
            # node.auspex_object = obj_instance
            node.type = the_name

            # See if names will be duplicated
            node_names = [i.label.toPlainText() for i in node_scene.items() if isinstance(i, Node)]
            nan = next_available_name(node_names, the_name)
            node.label.setPlainText(nan)

            node.setPos(node_scene.backdrop.mapFromParent(node_scene.last_click))
            node.setPos(node_scene.last_click)
            node_scene.addItem(node)
            return node

        # Add to class
        name = "create_"+("".join(comp_name.split()))
        setattr(node_scene, name, partial(create, comp, comp_name))
        func = getattr(node_scene, name)

        # Connect trigger for action
        def create_command(name=name,func=func,node_scene=node_scene):
            node_scene.undo_stack.push(CommandAddNode(name, func, node_scene))
        action.triggered.connect(create_command)
        node_scene.sub_menus["composites"].addAction(action)

def parse_quince_module(mod_name, mod, base_class, node_scene, submenu=None, mod_filter=None):
    new_objects = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f)
                                                            and issubclass(f, base_class)
                                                            and f != base_class}

    if mod_filter:
        new_objects = {n: f for n, f in new_objects.items() if mod_filter(f)}

    if len(new_objects) > 0:
        if submenu:
            sm = submenu.addMenu(mod_name)
        else:
            sm = node_scene.menu.addMenu(mod_name)
        node_scene.sub_menus[mod_name] = sm

    # Have the view keep track of the object so we can look them up easily
    node_scene.auspex_objects.update(new_objects)

    # These haven't been instantiated, so the input and output
    # connectors should be a simple list in the class dictionary
    for obj_name in sorted(new_objects.keys()):
        obj = new_objects[obj_name]

        # Create a QAction and add to the menu
        action = QAction(obj_name, node_scene)

        # Create function for dropping node on canvas
        def create(the_obj, the_name, the_category):
            node = Node(the_name, node_scene)
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
                node.is_instrument = True
                node.add_output(Connector('source', 'output'))

            # Set the class and module infor for PyQLab
            node.auspex_object = obj_instance
            node.type = the_name

            # See if names will be duplicated
            node_names = [i.label.toPlainText() for i in node_scene.items() if isinstance(i, Node)]
            nan = next_available_name(node_names, the_name)
            node.label.setPlainText(nan)

            node.setPos(node_scene.backdrop.mapFromParent(node_scene.last_click))
            node.setPos(node_scene.last_click)
            node_scene.addItem(node)
            return node

        # Add to class
        name = "create_"+("".join(obj_name.split()))
        setattr(node_scene, name, partial(create, obj, obj_name, mod_name))
        func = getattr(node_scene, name)

        # Connect trigger for action
        def create_command(name=name,func=func,node_scene=node_scene):
            node_scene.undo_stack.push(CommandAddNode(name, func, node_scene))
        action.triggered.connect(create_command)
        node_scene.sub_menus[mod_name].addAction(action)

def parse_quince_modules(node_scene):
    if NO_AUSPEX:
        return

    # Find all of the filters
    filter_modules = {
        name: importlib.import_module('auspex.filters.' + name)
        for loader, name, is_pkg in pkgutil.iter_modules(auspex_filt.__path__)
    }
    filter_modules.pop('filter') # We don't want the base class
    filter_modules.pop('elementwise') # This one is also an abstract base class

    # Find all of the instruments
    instrument_modules = {
        name: importlib.import_module('auspex.instruments.' + name)
        for loader, name, is_pkg in pkgutil.iter_modules(instr.__path__)
    }

    for mod_name in sorted(filter_modules.keys(), key=lambda s: s.lower()):
        mod = filter_modules[mod_name]
        parse_quince_module(mod_name, mod, Filter, node_scene)

    node_scene.menu.addSeparator()
    node_scene.instruments_menu = node_scene.menu.addMenu("instruments")
    node_scene.sub_menus["instruments"] = node_scene.instruments_menu

    for mod_name in sorted(instrument_modules.keys(), key=lambda s: s.lower()):
        mod = instrument_modules[mod_name]
        parse_quince_module(mod_name, mod, Instrument, node_scene,
                            submenu=node_scene.instruments_menu,
                            mod_filter=lambda m: hasattr(m, 'instrument_type') and "Digitizer" in m.instrument_type)