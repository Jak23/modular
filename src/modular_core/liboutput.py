import modular_core.libfundamental as lfu
import modular_core.libfiler as lf
import modular_core.libvtkoutput as lvtk
import modular_core.libtxtoutput as ltxt
import modular_core.libgeometry as lgeo
import modular_core.libsettings as lset

#from cStringIO import StringIO
import os
import time
try: import matplotlib.pyplot as plt
except ImportError: print 'matplotlib could not be imported! - output'
import numpy as np

import pdb

if __name__ == 'modular_core.liboutput':
	if lfu.gui_pack is None: lfu.find_gui_pack()
	lgm = lfu.gui_pack.lgm
	lgd = lfu.gui_pack.lgd

if __name__ == '__main__': print 'this is a library!'

def parse_output_plan_line(*args):
	data = args[0]
	ensem = args[1]
	parser = args[2]
	procs = args[3]
	routs = args[4]
	spl = [item.strip() for item in data.split(' : ')]
	dex = int(spl[0])
	if dex == 0: output = ensem.output_plan
	#else: output = procs[dex - 1].output
	elif dex <= len(procs): output = procs[dex - 1].output
	else: output = routs[dex - len(procs) - 1].output
	output.save_directory = spl[1]
	output.save_filename = spl[2]
	if 'plt' in spl[3]: output.output_plt = True
	else: output.output_plt = False
	if 'vtk' in spl[3]: output.output_vtk = True
	else: output.output_vtk = False
	if 'pkl' in spl[3]: output.output_pkl = True
	else: output.output_pkl = False
	if 'txt' in spl[3]: output.output_txt = True
	else: output.output_txt = False
	relevant = [item.strip() for item in spl[4].split(',')]
	if 'all' in relevant:
		if lfu.using_gui(): output.set_settables(0, ensem)
		output.targeted = output.get_target_labels()

	else: output.targeted = relevant

class writer(lfu.modular_object_qt):

	def __init__(self, parent = None, filenames = [], 
		label = 'another output writer', 
		base_class = lfu.interface_template_class(
						object, 'writer object'), 
		valid_base_classes = None, visible_attributes =\
					['label', 'base_class', 'filenames']):
		global valid_writers_base_classes
		if valid_base_classes is None:
			valid_base_classes = valid_writers_base_classes

		if base_class is None:
			base_class = lfu.interface_template_class(
									object, 'writer')

		self.filenames = filenames
		#lfu.modular_object_qt.__init__(self, label = label, 
		lfu.modular_object_qt.__init__(self, 
				visible_attributes = visible_attributes, 
				valid_base_classes = valid_base_classes, 
				parent = parent, base_class = base_class)
		self.axes_manager = plot_axes_manager(parent = self)
		self._children_ = [self.axes_manager]

	def __call__(self, *args): pass
	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 'filenames']

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		'''#this has never actually been implemeneted
		classes = [template._class for template 
					in self.valid_base_classes]
		tags = [template._tag for template 
				in self.valid_base_classes]
		self.widg_templates.append(
			lgm.interface_template_gui(
				widget_mason = recaster, 
				widget_layout = 'vert', 
				key = ['_class'], 
				instance = [[self.base_class, self]], 
				widget = ['rad'], 
				hide_none = [True], 
				box_label = 'Write Method', 
				initial = [self.base_class._tag], 
				possibles = [tags], 
				possible_objs = [classes], 
				sizer_position = (1, 0)))
		'''
		super(writer, self).set_settables(*args, from_sub = True)

class writer_vtk(writer):

	def __init__(self, parent = None, 
		filenames = [], iteration_resolution = 1, 
		label = 'another vtk output writer', 
		base_class = lfu.interface_template_class(
					object, 'vtk writer object')):
		self.filenames = filenames
		self.iteration_resolution = iteration_resolution
		writer.__init__(self, label = label, 
			parent = parent, base_class = base_class)

	def __call__(self, system, vtk_filename, specifics):
		lvtk.write_unstructured(system, vtk_filename, specifics)

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 
					'filenames', 'iteration_resolution']

class writer_pkl(writer):

	def __init__(self, parent = None, 
		filenames = [], iteration_resolution = 1, 
		label = 'another pkl output writer', 
		base_class = lfu.interface_template_class(
					object, 'pkl writer object')):
		self.filenames = filenames
		self.iteration_resolution = iteration_resolution
		writer.__init__(self, label = label, 
			parent = parent, base_class = base_class)

	def __call__(self, *args):
		system = args[0]
		filename = args[1]
		try:
			lf.save_pkl_object(system, filename)

		except IOError:
			print 'failed to output .pkl file'

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 'filenames']

class writer_txt(writer):

	def __init__(self, parent = None, filenames = [], 
		label = 'another csv output writer', 
		base_class = lfu.interface_template_class(
					object, 'txt writer object')):
		self.filenames = filenames
		writer.__init__(self, label = label, 
			parent = parent, base_class = base_class)

	def __call__(self, *args):
		system = args[0]
		filename = args[1]
		specifics = args[2]
		ltxt.write_csv(system, filename, specifics)

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 'filenames']

class plot_axes_manager(lfu.modular_object_qt):

	_children_ = []

	def grab_info_from_output_plan_parent(self):
		try: self.x_title = self.parent.parent.parent.x_title
		except: self.x_title = 'x-title'
		try: self.y_title = self.parent.parent.parent.y_title
		except: self.y_title = 'y-title'
		try: self.title = self.parent.parent.parent.title
		except: self.title = 'title'

	def use_line_plot(self):
		if self.parent.parent.parent.use_line_plot:
			return True

		else: return False

	def use_color_plot(self):
		if self.parent.parent.parent.use_color_plot:
			return True

		else: return False

	def use_bar_plot(self):
		if self.parent.parent.parent.use_bar_plot:
			return True

		else: return False

	def set_settables(self, *args, **kwargs):
		self.handle_widget_inheritance(*args, **kwargs)
		super(plot_axes_manager, self).set_settables(
							*args, from_sub = True)

class writer_plt(writer):

	def __init__(self, parent = None, 
		filenames = [], iteration_resolution = 1, 
		label = 'another plt output writer', 
		base_class = lfu.interface_template_class(
					object, 'plt writer object')):
		self.filenames = filenames
		self.iteration_resolution = iteration_resolution
		writer.__init__(self, label = label, 
			parent = parent, base_class = base_class)

	def get_plt_window(self):
		#when you make the plot window, are you aware of every type
		# of data object it will see?
		# if so you can impost plot_types from here
		plot_types = []
		if self.axes_manager.use_color_plot():
			plot_types.append('color')

		if self.axes_manager.use_color_plot():
			plot_types.append('surface')

		if self.axes_manager.use_line_plot():
			plot_types.append('lines')

		if self.axes_manager.use_bar_plot():
			plot_types.append('bars')

		self.axes_manager.grab_info_from_output_plan_parent()
		self.plt_window = lgd.plot_window(
			title = self.parent.parent.label, 
			plot_types = plot_types)

	def sanitize(self, *args, **kwargs):
		self.plt_window = None
		#self.plotter = None
		writer.sanitize(self, *args, **kwargs)

	def __call__(self, data_container, plt_filename, specifics):
		#when the plotter is called, it should append a page appropriately
		self.plotter(data_container, plt_filename, specifics)

	def plotter(self, data_container, plt_filename, specifics):
		self.plt_window.set_plot_info(data_container, 
			plt_filename, specifics, title = self.axes_manager.title, 
			x_ax_title = self.axes_manager.x_title, 
			y_ax_title = self.axes_manager.y_title)

	def set_uninheritable_settables(self, *args, **kwargs):
		self.visible_attributes = ['label', 'base_class', 'filenames']

class output_plan(lfu.plan):

	#any mobj which owns this mobj needs to have .capture_targets
	def __init__(self, label = 'another output plan', use_plan = True, 
		visible_attributes = ['label', 'use_plan', 'output_vtk', 
							'output_pkl', 'output_txt', 'output_plt', 
							'save_directory', 'save_filename', 
							'filenames', 'directories', 'targeted'], 
					save_directory = '', save_filename = '', 
											parent = None):
		self.__dict__ = lfu.dictionary()
		self.writers = [	writer_vtk(parent = self), 
							writer_pkl(parent = self), 
							writer_txt(parent = self), 
							writer_plt(parent = self)	]
		self.flat_data = True
		#if label is not 'another output plan': one_of_a_kind = True
		self.targeted = []	#lists of strings to list of scalars
		self.outputs = [[], [], [], []]	#strings pointing to targeted scalars
		self.save_directory = save_directory
		self.save_filename = save_filename
		self.filenames = {'vtk filename': '', 'pkl filename': '', 
						'txt filename': '', 'plt filename': ''}
		self.directories = {'vtk directory': '', 'pkl directory': '', 
							'txt directory': '', 'plt directory': ''}
		op_vtk = lset.get_setting('output_vtk')
		op_pkl = lset.get_setting('output_pkl')
		op_txt = lset.get_setting('output_txt')
		op_plt = lset.get_setting('output_plt')
		if not op_vtk is None: self.output_vtk = op_vtk
		else: self.output_vtk = False
		if not op_pkl is None: self.output_pkl = op_pkl
		else: self.output_pkl = False
		if not op_txt is None: self.output_txt = op_txt
		else: self.output_txt = False
		if not op_plt is None: self.output_plt = op_plt
		else: self.output_plt = False
		self.default_targets_vtk = True
		self.default_targets_pkl = True
		self.default_targets_txt = True
		self.default_targets_plt = True
		self.default_paths_vtk = True
		self.default_paths_pkl = True
		self.default_paths_txt = True
		self.default_paths_plt = True
		lfu.plan.__init__(self, label = label, use_plan = True, 
			visible_attributes = visible_attributes, parent = parent)
		self._children_ = self.writers
		self.__dict__.create_partition('template owners', ['writers'])

	def to_string(self):
		#0 : C:\Users\bartl_000\Desktop\Work\Modular\chemicallite\output : ensemble_output : none : all
		if self.label.startswith('Simulation'): numb = '0'
		else:
			procs = lfu.grab_mobj_names(
				self.parent.parent.post_processes)
			numb = str(procs.index(self.parent.label) + 1)

		plot_types = [item for item, out_item in 
			zip(['vtk', 'pkl', 'txt', 'plt'], 
			[self.output_vtk, self.output_pkl, 
			self.output_txt, self.output_plt]) if out_item]
		if not plot_types: plots = 'none'
		else: plots = ', '.join(plot_types)
		targs = self.get_target_labels()
		if not self.targeted: targs = 'none'
		elif self.targeted == targs: targs = 'all'
		else: targs = ', '.join(self.targeted)
		return '\t' + ' : '.join([numb, self.save_directory, 
						self.save_filename, plots, targs])

	def must_output(self, *args, **kwargs):
		return True in [self.output_vtk, self.output_pkl, 
						self.output_txt, self.output_plt]

	def update_filenames(self, *args, **kwargs):
		self.save_filename = lfu.increment_filename(self.save_filename)
		lfu.modular_object_qt(self).update_filenames(self.filenames)

	def find_proper_paths(self):
		propers = {}
		output_type_id = ['vtk', 'pkl', 'txt', 'plt']
		output_type_bool = [self.default_paths_vtk, 
							self.default_paths_pkl, 
							self.default_paths_txt, 
							self.default_paths_plt]
		for _id, _bool in zip(output_type_id, output_type_bool):
			if _bool:
				propers[_id] = os.path.join(self.save_directory, 
								self.save_filename + '.' + _id)

			else:
				propers[_id] = os.path.join(
							self.directories[_id + ' directory'],
							self.filenames[_id + ' filename'], '.' + _id)

		for _id, prop in propers.items():
			if not os.path.exists(prop):
				prope = None
				pa_dex = -2
				out = False
				fil = prop.split(os.path.sep)[-1]
				while prope is None and not out:
					try:
						dat_file = prop.split(os.path.sep)[pa_dex]
						prope = lfu.resolve_filepath(
								dat_file, isdir = True)
					except IndexError: out = True
					pa_dex -= 1
				propers[_id] = os.path.join(prope, fil)

		return propers

	def find_proper_targets(self):
		propers = []
		output_type_bool = [self.default_targets_vtk, 
							self.default_targets_pkl, 
							self.default_targets_txt, 
							self.default_targets_plt]
		for dex, _bool in enumerate(output_type_bool):
			if _bool: propers.append(self.targeted)
			else: propers.append(self.outputs[dex])
		return propers

	def enact_plan(self, *args):
		system = args[0]
		if hasattr(system, 'override_targets'):
			if system.override_targets:
				proper_targets = [system.override_targets]*4
			else: proper_targets = self.find_proper_targets()
		else: proper_targets = self.find_proper_targets()
		to_be_outted = []
		if not self.flat_data:	#if the list of data objects is not flat (system.data is the list)
			#self.to_be_outted has a 3rd element pointing to system within non-flat pool
			#system will be an object with attribute .data but .data is a non-flat list!
			#put each data list into a flat list of objects with flat lists for data attributes

			#targs = self.get_target_labels()
			for traj in system.data:
				data_container = lfu.data_container(data = traj)
				self.update_filenames()
				proper_paths = self.find_proper_paths()
				if self.output_vtk:
					to_be_outted.append((proper_paths['vtk'], 
										0, data_container))

				if self.output_pkl:
					to_be_outted.append((proper_paths['pkl'], 
										1, data_container))

				if self.output_txt:
					to_be_outted.append((proper_paths['txt'], 
										2, data_container))

				if self.output_plt:
					to_be_outted.append((proper_paths['plt'], 
										3, data_container))

			if 3 in [out[1] for out in to_be_outted]:
					self.writers[3].get_plt_window()

			[self.writers[out[1]](out[2], out[0], 
				proper_targets[out[1]]) for out in to_be_outted]

			if 3 in [out[1] for out in to_be_outted]:
					self.writers[3].plt_window()

		else:
			self.update_filenames()
			proper_paths = self.find_proper_paths()
			#if the list of data objects is flat (system.data is the list)
			#self.to_be_outted has only 2 elements since data is already flat
			if self.output_vtk:
				to_be_outted.append((proper_paths['vtk'], 0))

			if self.output_pkl:
				to_be_outted.append((proper_paths['pkl'], 1))

			if self.output_txt:
				to_be_outted.append((proper_paths['txt'], 2))

			if self.output_plt:
				to_be_outted.append((proper_paths['plt'], 3))

			if 3 in [out[1] for out in to_be_outted]:
					self.writers[3].get_plt_window()

			[self.writers[out[1]](system, out[0], 
				proper_targets[out[1]]) for out in to_be_outted]

			if 3 in [out[1] for out in to_be_outted]:
					self.writers[3].plt_window()

	def verify_nonempty_save_directory(self):
		if not self.parent is None:
			if self.save_directory == None or self.save_directory == '':
				try:
					self.save_directory = os.path.join(os.getcwd(), 
									self.parent.module, 'output')
				except AttributeError:
					try:
						self.save_directory = os.path.join(os.getcwd(), 
								self.parent._modu_program_, 'output')
					except AttributeError:
						self.save_directory = os.getcwd()

	def verify_nonempty_save_filename(self):
		if self.save_filename == None or self.save_filename == '':
			self.save_filename = '_'.join(
				['_'.join(self.parent.label.split()), 'output'])

	def get_target_labels(self, *args, **kwargs):
		if args: ensem = args[0]
		if self.parent is None:
			target_labels = ensem.run_params['plot_targets']

		else:
			try: target_labels = self.parent.run_params['plot_targets']
			except AttributeError:
				target_labels = self.parent.capture_targets

		return target_labels

	def set_settables(self, *args, **kwargs):
		#ensem = args[1]
		target_labels = self.get_target_labels(*args, **kwargs)
		#set_settables gets called bottom up
		# always have issues when childs templates depend on information
		#  which is updated in the parents set_settables function

		self.targeted = lfu.intersect_lists(self.targeted, target_labels)
		for dex in range(len(self.outputs)):
			self.outputs[dex] = lfu.intersect_lists(
					self.outputs[dex], target_labels)

		self.handle_widget_inheritance(*args, **kwargs)
		self.writers[0].set_settables(*args, **kwargs)
		self.writers[1].set_settables(*args, **kwargs)
		self.writers[2].set_settables(*args, **kwargs)
		self.writers[3].set_settables(*args, **kwargs)
		plt_page_template = lgm.interface_template_gui(
				panel_label = 'plt Writer Options', 
				panel_scrollable = True, 
				panel_position = (1, 3), 
				widgets = ['panel', 'check_set', 'check_set', 
						'directory_name_box', 'file_name_box'], 
				box_labels = [None, 'plt Plot Targets', '', 
					'plt Save Directory', 'plt Base Filename'], 
				append_instead = [None, True, False, None, None], 
				provide_master = [None, True, False, None, None], 
				instances = [None, [self], [self, self], 
					[self.directories], [self.filenames]], 
				rewidget = [None, [True], [True], [True], [True]], 
				keys = [None, ['outputs'], 
				#there is likely a bug with the 'outputs' check set ->
				#	it likely screws up nesting
				#	doesnt handle inst_is_list = True correctly
					['default_targets_plt', 'default_paths_plt'], 
							['pkl directory'], ['pkl filename']], 
				instance_is_dict = [None, None, None, 
						(True, self), (True, self)], 
				initials = [None, None, None, 
					[self.directories['plt directory']], 
					[self.filenames['plt filename']]], 
				labels = [None, target_labels, 
						['Use Default Plot Targets', 
						'Use Default Output Path'], 
						['Choose Directory'], ['Choose Filename']], 
				templates = [self.writers[3].widg_templates, 
								None, None, None, None])
		txt_page_template = lgm.interface_template_gui(
				panel_label = 'csv Writer Options', 
				panel_scrollable = True, 
				widgets = ['panel', 'check_set', 'check_set', 
						'directory_name_box', 'file_name_box'], 
				box_labels = [None, 'csv Plot Targets', '', 
					'csv Save Directory', 'csv Base Filename'], 
				append_instead = [None, True, False, None, None], 
				provide_master = [None, True, False, None, None], 
				instances = [None, [self], [self, self], 
					[self.directories], [self.filenames]], 
				rewidget = [None, [True], [True], [True], [True]], 
				keys = [None, ['outputs'], 
				#there is likely a bug with the 'outputs' check set ->
				#	it likely screws up nesting
				#	doesnt handle inst_is_list = True correctly
					['default_targets_txt', 'default_paths_txt'], 
							['txt directory'], ['txt filename']], 
				instance_is_dict = [None, None, None, 
						(True, self), (True, self)], 
				initials = [None, None, None, 
					[self.directories['txt directory']], 
					[self.filenames['txt filename']]], 
				labels = [None, target_labels, 
						['Use Default Plot Targets', 
						'Use Default Output Path'], 
						['Choose Directory'], ['Choose Filename']], 
				templates = [self.writers[2].widg_templates, 
								None, None, None, None])
		pkl_page_template = lgm.interface_template_gui(
				panel_label = 'pkl Writer Options', 
				panel_scrollable = True, 
				widgets = ['panel', 'check_set', 'check_set', 
						'directory_name_box', 'file_name_box'], 
				box_labels = [None, 'pkl Plot Targets', '', 
					'pkl Save Directory', 'pkl Base Filename'], 
				append_instead = [None, True, False, None, None], 
				provide_master = [None, True, False, None, None], 
				instances = [None, [self], [self, self], 
					[self.directories], [self.filenames]], 
				rewidget = [None, [True], [True], [True], [True]], 
				keys = [None, ['outputs'], 
					['default_targets_pkl', 'default_paths_pkl'], 
							['pkl directory'], ['pkl filename']], 
				instance_is_dict = [None, None, None, 
						(True, self), (True, self)], 
				instance_is_list = [None, (True, 1), None, None, None], 
				initials = [None, None, None, 
					[self.directories['pkl directory']], 
					[self.filenames['pkl filename']]], 
				labels = [None, target_labels, 
						['Use Default Plot Targets', 
						'Use Default Output Path'], 
						['Choose Directory'], ['Choose Filename']], 
				templates = [self.writers[1].widg_templates, 
							None, None, None, None])
		vtk_page_template = lgm.interface_template_gui(
				panel_label = 'vtk Writer Options', 
				panel_scrollable = True, 
				widgets = ['panel', 'check_set', 'check_set', 
						'directory_name_box', 'file_name_box'], 
				box_labels = [None, 'vtk Plot Targets', '', 
					'vtk Save Directory', 'vtk Base Filename'], 
				append_instead = [None, True, False, None, None], 
				provide_master = [None, True, False, None, None], 
				instances = [None, [self], [self, self], 
					[self.directories], [self.filenames]], 
				rewidget = [None, [True], [True], [True], [True]], 
				keys = [None, ['outputs'], 
					['default_targets_vtk', 'default_paths_vtk'], 
							['vtk directory'], ['vtk filename']], 
				instance_is_dict = [None, None, None, 
						(True, self), (True, self)], 
				initials = [None, None, None, 
					[self.directories['vtk directory']], 
					[self.filenames['vtk filename']]], 
				labels = [None, target_labels, 
						['Use Default Plot Targets', 
						'Use Default Output Path'], 
						['Choose Directory'], ['Choose Filename']], 
				templates = [self.writers[0].widg_templates, 
								None, None, None, None])
		writers_splitter_template = lgm.interface_template_gui(
				widgets = ['splitter'], 
				verbosities = [2], 
				orientations = [['horizontal']], 
				templates = [[plt_page_template, txt_page_template, 
							pkl_page_template, vtk_page_template]])
		top_templates = []
		top_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 3), 
				widgets = ['check_set'], 
				append_instead = [True], 
				provide_master = [True], 
				instances = [[self]],
				keys = [['targeted']],
				labels = [target_labels], 
				box_labels = ['Default Plot Targets']))
		self.verify_nonempty_save_filename()
		top_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 1), 
				widgets = ['file_name_box'], 
				keys = [['save_filename']], 
				instances = [[self]], 
				initials = [[self.save_filename, 
					'Possible Outputs (*.vtk *.csv)']], 
				labels = [['Choose Filename']], 
				box_labels = ['Default Base Filename']))
		self.verify_nonempty_save_directory()
		top_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 0), 
				widgets = ['directory_name_box'], 
				keys = [['save_directory']], 
				instances = [[self]], 
				initials = [[self.save_directory, None, 
					os.path.join(os.getcwd(), 'resources')]], 
				labels = [['Choose Directory']], 
				box_labels = ['Default Save Directory']))
		top_templates.append(
			lgm.interface_template_gui(
				panel_position = (0, 2), 
				widgets = ['check_set'], 
				append_instead = [False], 
				instances = [[self]*4],
				keys = [['output_vtk', 'output_pkl', 
						'output_txt', 'output_plt']],
				labels = [['Output .vtk files', 'Output .pkl files', 
						'Output .csv files', 'Output .plt files']], 
				box_labels = ['Output Types']))
		top_template = lgm.interface_template_gui(
				widgets = ['panel'], 
				scrollable = [True], 
				templates = [top_templates])
		self.widg_templates.append(
			lgm.interface_template_gui(
				widgets = ['splitter'], 
				orientations = [['vertical']], 
				templates = [[top_template, 
					writers_splitter_template]]))
		lfu.modular_object_qt.set_settables(
				self, *args, from_sub = True)

valid_writers_base_classes = [
	lfu.interface_template_class(
	writer_vtk, 'vtk'), 
	lfu.interface_template_class(
	writer_pkl, 'pickle'), 
	lfu.interface_template_class(
	writer_txt, 'text'), 
	lfu.interface_template_class(
	writer_plt, 'plot')]



