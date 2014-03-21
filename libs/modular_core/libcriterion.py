import libs.modular_core.libfundamental as lfu

import sys
import types
from copy import deepcopy as copy

import pdb

class criterion(lfu.modular_object_qt):

	#ABSTRACT
	def __init__(	self, parent = None, verify_pass_func = None, 
					base_class = None, bRelevant = True, 
					label = 'criterion', 
					valid_base_classes = None, 
					visible_attributes = ['label', 
						'base_class', 'bRelevant']	):
		if valid_base_classes is None:
			global valid_criterion_base_classes
			valid_base_classes = valid_criterion_base_classes

		if base_class is None:
			base_class = lfu.interface_template_class(
							object, 'criterion abstract')

		if verify_pass_func is not None:
			self.verify_pass = verify_pass_func

		self.bRelevant = bRelevant	#checking relevance is the
				#responsibility of the owner of the criterion!!
		lfu.modular_object_qt.__init__(self, parent= parent, 
			label = label, visible_attributes = visible_attributes, 
							valid_base_classes = valid_base_classes, 
											base_class = base_class)
		self._children_ = []

	def verify_pass(self, *args, **kwargs):
		print 'abstract criterion always returns True'
		return True

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (2, 0), 
				widgets = ['check_set'], 
				append_instead = [False],
				instances = [[self]], 
				keys = [['bRelevant']], 
				labels = [['Use This Criterion']]))
		recaster = lgm.recasting_mason(parent = args[0])
		classes = [template._class for template 
					in self.valid_base_classes]
		tags = [template._tag for template 
				in self.valid_base_classes]
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 0), 
				widgets = ['radio'], 
				mason = recaster, 
				keys = [['_class']], 
				instances = [[(self.base_class, self)]], 
				box_labels = ['Criterion Type'], 
				labels = [tags], 
				initials = [[self.base_class._tag]]))
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['text'], 
				keys = [['label']], 
				instances = [[self]], 
				initials = [[self.label]], 
				box_labels = ['Criterion Name']))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

class criterion_iteration(criterion):

	def __init__(self, parent = None, max_iterations = 1000, base_class = None, 
			label = 'iteration criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'max_iterations']):
		if base_class is None:
			base_class = lfu.interface_template_class(
				criterion_iteration, 'iteration limit')
		criterion.__init__(self, parent = parent, label = label, 
										base_class = base_class)
		self.max_iterations = max_iterations
		self._children_ = []

	def to_string(self):
		return '\titeration limit : ' + str(self.max_iterations)

	def initialize(self, *args, **kwargs):
		self.max_iterations = float(self.max_iterations)

	def verify_pass(self, *args):
		obj = args[0]
		try:
			if obj.iteration >= self.max_iterations:
				#print 'criterion: passed iteration limit'
				return True

		except AttributeError:
			print 	'iteration criterion applied \
					\n to object without .iteration'
			return True

		return False

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
							'bRelevant', 'max_iterations']

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[False]], 
				initials = [[int(self.max_iterations)]], 
				minimum_values = [[0]], 
				maximum_values = [[sys.maxint]], 
				instances = [[self]], 
				keys = [['max_iterations']], 
				box_labels = ['Iteration Limit']))
		criterion.set_settables(self, *args, from_sub = True)

class criterion_sim_time(criterion):

	def __init__(self, parent = None, max_time = 100.0, base_class =\
			lfu.interface_template_class(object, 'time limit'), 
			label = 'time limit criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'max_time']):
		criterion.__init__(self, parent = parent, label = label, 
										base_class = base_class)
		self.max_time = max_time

	def to_string(self):
		return '\ttime limit : ' + str(self.max_time)

	def initialize(self, *args, **kwargs):
		self.max_time = float(self.max_time)

	def verify_pass(self, system):
		if self.max_time <= system.time[-1]:
			#print 'criterion: passed time limit'
			return True

		return False

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
								'bRelevant', 'max_time'	]
		#this has to be overridden even if this class lacks
		# its own uninheritable settables

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[True]], 
				initials = [[float(self.max_time)]], 
				minimum_values = [[0.0]], 
				maximum_values = [[sys.float_info.max]], 
				instances = [[self]], 
				keys = [['max_time']], 
				box_labels = ['Max Simulation Time']))
		super(criterion_sim_time, self).set_settables(
								*args, from_sub = True)

class criterion_capture_count(criterion):

	def __init__(self, parent = None, max_captures = 100.0, base_class =\
		lfu.interface_template_class(object, 'capture limit'), 
			label = 'capture limit criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'max_captures']):
		criterion.__init__(self, parent = parent, label = label, 
										base_class = base_class)
		self.max_captures = max_captures

	def to_string(self):
		return '\tcapture limit : ' + str(self.max_captures)

	def initialize(self, *args, **kwargs):
		self.max_captures = int(self.max_captures)

	def verify_pass(self, system):
		try:
			if len(system.data[0].scalers) >= self.max_captures:
				print 'criterion: passed capture count limit'
				return True

			return False

		except IndexError:
			print 'capture count criterion with no capture targets!'
			return True

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
							'bRelevant', 'max_captures']
		#this has to be overridden even if this class lacks
		# its own uninheritable settables

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[False]], 
				initials = [[int(self.max_captures)]], 
				minimum_values = [[0]], 
				maximum_values = [[sys.maxint]], 
				instances = [[self]], 
				keys = [['max_captures']], 
				box_labels = ['Capture Count Limit']))
		super(criterion_capture_count, self).set_settables(
									*args, from_sub = True)

class criterion_scaler_increment(criterion):

	def __init__(self, parent = None, increment = 10.0, key = 'time', 
			keys = ['iteration', 'time'], 
			base_class = lfu.interface_template_class(
							object, 'scaler increment'), 
			label = 'scaler increment criterion', visible_attributes =\
			['label', 'base_class', 'bRelevant', 'key', 'increment']):
		criterion.__init__(self, parent = parent, label = label, 
										base_class = base_class)
		#self.key expected to match dater.label
		self.key = key
		self.keys = keys
		self.increment = increment

	def to_string(self):
		return '\tspecies scaler increment : ' + \
			str(self.increment) + ' : ' + self.key

	def initialize(self): self.increment = float(self.increment)
	def find_last_value(self, system):
		try:
			try:
				#this works for lists
				last_value = system.__dict__[self.key][-1]

			except TypeError:
				#if its just a value instead of a list
				last_value = system.__dict__[self.key]

			return last_value

		except:
			print 'criterion possibly not working!'
			pdb.set_trace()

	def verify_pass(self, system):
		last_value = self.find_last_value(system)
		scaldex = [dater.label == self.key 
					for dater in system.data].index(True)
		return abs(last_value - system.data[scaldex].scalers[-1])\
												>= self.increment

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
				'bRelevant', 'key', 'keys', 'increment']

	def set_settables(self, *args, **kwargs):
		ensem = args[0]
		frame = args[1]
		self.handle_widget_inheritance(*args, from_sub = False)
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['spin'], 
				doubles = [[True]], 
				initials = [[float(self.increment)]], 
				minimum_values = [[0.0]], 
				maximum_values = [[sys.float_info.max]], 
				instances = [[self]], 
				keys = [['increment']], 
				box_labels = ['Increment']))
		self.widg_templates.append(
			lgm.interface_template_gui(
				panel_position = (1, 1), 
				widgets = ['radio'], 
				labels = [self.keys], 
				initials = [[self.key]], 
				instances = [[self]], 
				keys = [['key']], 
				box_labels = ['Scaler to Check']))
		super(criterion_scaler_increment, self).set_settables(
										*args, from_sub = True)

#MUST create an eval function criterion

valid_criterion_base_classes = [
		lfu.interface_template_class(
	criterion_sim_time, 'time limit'), 
		lfu.interface_template_class(
	criterion_iteration, 'iteration limit'), 
		lfu.interface_template_class(
	criterion_capture_count, 'capture limit'), 
		lfu.interface_template_class(
	criterion_scaler_increment, 'scaler increment')]

if __name__ == 'libs.modular_core.libcriterion':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd
	lgb = lfu.gui_pack.lgb

if __name__ == '__main__': print 'this is a library!'



