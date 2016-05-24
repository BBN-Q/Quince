
import importlib
import pkgutil
import inspect

try:
	import pycontrol
	import pycontrol.filters as filt
	from pycontrol.filters.filter import Filter
except:
	print("Could not locate pycontrol in the python path.")

modules = {
    name: importlib.import_module('pycontrol.filters.' + name)
    for loader, name, is_pkg in pkgutil.walk_packages(filt.__path__)
}
modules.pop('filter') # We don't want the base class

filters = {}
for mod_name, mod in modules.items():
	print("Finding all filter objects in module " + mod_name + ":")
	new_filters = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f) and issubclass(f, Filter) and f != Filter}
	filters.update(new_filters)
	print("Found: {}".format(list(new_filters.keys())))

	# These haven't been instantiated, so the input and output
	# connectors should be a simple list in the class dictionary
	for n, f in new_filters.items():
		print('Input Connectors: '  + str(f._input_connectors))
		print('Output Connectors: ' + str(f._output_connectors))
