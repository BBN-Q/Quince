import importlib
import pkgutil
import inspect
import json
import os.path

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


# Make the base directory:
nodes_dirname = "pycontrol-nodes"
os.makedirs(nodes_dirname)
os.chdir(nodes_dirname)

filters = {}
for mod_name, mod in modules.items():
	print("Finding all filter objects in module " + mod_name + ":")
	os.makedirs(mod_name)

	new_filters = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f) and issubclass(f, Filter) and f != Filter}
	filters.update(new_filters)
	print("Found: {}".format(list(new_filters.keys())))

	# These haven't been instantiated, so the input and output
	# connectors should be a simple list in the class dictionary
	for n, f in new_filters.items():
		print('Input Connectors: '  + str(f._input_connectors))
		print('Output Connectors: ' + str(f._output_connectors))
		
		# Start a dictionary for JSON output
		j = {}
		j["name"] = mod_name
		j["outputs"] = f._output_connectors
		j["inputs"] = f._input_connectors
		j["parameters"] = []

		with open("{}/{}.json".format(mod_name, n), 'w') as f:
			json.dump(j, f, sort_keys=True, indent=4, separators=(',', ': '))

# # Now create the JSON



	

# 	{
# "name": "Boxcar Filter",
# "outputs": ["Integrated"],
# "inputs": ["Data"],
# "parameters": [
# 	{"name": "Sample Rate", "type": "float", "increment": 100e6, "snap": true, "low":100e6, "high": 4.0e9, "tip": "Samp/sec"},
# 	{"name": "I.F. Freq.", "type": "float", "increment": 1e6, "snap": true, "low": 0, "high": 0.1e9, "tip": "Hz"},
# 	{"name": "Boxcar Start", "type": "int", "increment": 1, "snap": true, "low": 1, "high": 50, "tip": "1 is no decimation."},
# 	{"name": "Boxcar Stop", "type": "int", "increment": 1, "snap": true, "low": 1, "high": 1000, "tip": "1 is no decimation."}
# 	]
# }