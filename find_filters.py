import importlib
import pkgutil
import inspect
import json
import os.path

try:
	import pycontrol
	import pycontrol.filters as filt
	import pycontrol.instruments as instr
	from pycontrol.filters.filter import Filter
	from pycontrol.instruments.instrument import Instrument, SCPIInstrument, CLibInstrument
except:
	print("Could not locate pycontrol in the python path.")

# Find all of the filters
filter_modules = {
    name: importlib.import_module('pycontrol.filters.' + name)
    for loader, name, is_pkg in pkgutil.walk_packages(filt.__path__)
}
filter_modules.pop('filter') # We don't want the base class

# Find all of the instruments
instrument_vendors = {
    name: importlib.import_module('pycontrol.instruments.' + name)
    for loader, name, is_pkg in pkgutil.iter_modules(instr.__path__)
}

# Make the base directory:
nodes_dirname = "pycontrol-nodes"
os.makedirs(nodes_dirname)
os.chdir(nodes_dirname)

for mod_name, mod in filter_modules.items():
	print("Finding all filter objects in module " + mod_name + ":")
	os.makedirs(mod_name)

	new_filters = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f)
															and issubclass(f, Filter) 
															and f != Filter}
	print("Found: {}".format(list(new_filters.keys())))

	# These haven't been instantiated, so the input and output
	# connectors should be a simple list in the class dictionary
	for n, f in new_filters.items():
		print('Input Connectors: '  + str(f._input_connectors))
		print('Output Connectors: ' + str(f._output_connectors))
		
		# Start a dictionary for JSON output
		j = {}
		j["name"] =  n
		j["outputs"] = f._output_connectors
		j["inputs"] = f._input_connectors
		j["parameters"] = []
		j["x__class__"] = n
		j["x__module__"] = "MeasFilters"

		with open("{}/{}.json".format(mod_name, n), 'w') as f:
			json.dump(j, f, sort_keys=True, indent=4, separators=(',', ': '))

# Create the instruments directory
instruments_dirname = "instruments"
os.makedirs(instruments_dirname)
os.chdir(instruments_dirname)

for mod_name, mod in instrument_vendors.items():
	print("Finding all filter objects in module " + mod_name + ":")

	new_instr = {n: f for n, f in mod.__dict__.items() if inspect.isclass(f)
														and issubclass(f, Instrument)
														and f != Instrument
														and f != SCPIInstrument
														and f != CLibInstrument}
	print("Found: {}".format(list(new_instr.keys())))

	has_at_least_one_digitizer = False

	# These haven't been instantiated, so the input and output
	# connectors should be a simple list in the class dictionary
	for n, f in new_instr.items():
		if hasattr(f, 'instrument_type') and f.instrument_type == "Digitizer":
			if not has_at_least_one_digitizer:
				os.makedirs(mod_name)
			has_at_least_one_digitizer = True
			# Start a dictionary for JSON output
			j = {}
			j["name"] =  n
			j["outputs"] = ["source"]
			j["inputs"] = []
			j["parameters"] = []
			j["x__class__"] = n
			j["x__module__"] = "instruments.Digitizers"

			with open("{}/{}.json".format(mod_name, n), 'w') as f:
				json.dump(j, f, sort_keys=True, indent=4, separators=(',', ': '))
