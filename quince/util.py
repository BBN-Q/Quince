# coding: utf-8
# Raytheon BBN Technologies 2016
# Contributiors: Graham Rowlands
#
# This file contains utility functions for quince

from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
import re

def next_available_name(node_names, label):
	# Check node_names and see if we can find 'label ###'
	# If we can, then we'll return the next available ###+1
	try:
		match_attempts = [re.match(label+' (\d+)', nn) for nn in node_names]
		match_attempts[:] = [int(m.group(1)) for m in match_attempts if m != None]
		if len(match_attempts) == 0:
			return label+" 1"
		else:
			return label+" {:d}".format(sorted(match_attempts)[-1]+1)
	except:
		return label + ' ?'

def strip_numbers(label):
	try:
		match_attempt = re.match('(.*?)(\d+)$', label)
		stripped = match_attempt.group(1).strip()
	except:
		stripped = label
	return stripped

class dummy_object_QPointF(QObject):
	"""Fake object for animation purposes"""
	def __init__(self, getter, setter):
		super(dummy_object_QPointF, self).__init__()
		self.getter, self.setter = getter, setter
	def dummy_get(self):
		return self.getter()
	def dummy_set(self, value):
		self.setter(value)
	dummy = Property(QPointF, dummy_get, dummy_set) 

class dummy_object_float(QObject):
	"""Fake object for animation purposes"""
	def __init__(self, getter, setter):
		super(dummy_object_float, self).__init__()
		self.getter, self.setter = getter, setter
	def dummy_get(self):
		return self.getter()
	def dummy_set(self, value):
		self.setter(value)
	dummy = Property(float, dummy_get, dummy_set) 