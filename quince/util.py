# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains utility functions for quince

import re

def next_available_name(node_names, label):
	# Check node_names and see if we can find 'label ###'
	# If we can, then we'll return the next available ###+1
	match_attempts = [re.match(label+' (\d+)', nn) for nn in node_names]
	try:
		match_attempts[:] = [int(m.group(1)) for m in match_attempts if m != None]
		if len(match_attempts) == 0:
			return label+" 1"
		else:
			return label+" {:d}".format(sorted(match_attempts)[-1]+1)
	except:
		return label + '???'

def strip_numbers(label):
	match_attempt = re.match('(.*?)(\d+)$', label)
	try:
		stripped = match_attempt.group(1).strip()
	except:
		stripped = label + '???'
	return stripped

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())