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
	match_attempts[:] = [int(m.group(1)) for m in match_attempts if m != None]

	if len(match_attempts) == 0:
		return label+" 1"
	else:
		return label+" {:d}".format(sorted(match_attempts)[-1]+1)

def strip_numbers(label):
	match_attempt = re.match('(.*?)(\d+)$', label)
	return match_attempt.group(1).strip()
