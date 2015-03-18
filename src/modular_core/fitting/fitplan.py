import modular_core.fundamental as lfu
import modular_core.data.batch_target as dba
import modular_core.settings as lset

import modular_core.io.libfiler as lf
import modular_core.fitting.routine_abstract as fab

import pdb,os,sys,types,time,math,random,traceback
import numpy as np

if __name__ == 'modular_core.fitting.fitplan':
    lfu.check_gui_pack()
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    lgb = lfu.gui_pack.lgb
if __name__ == '__main__':print 'fitplan of modular_core'

###############################################################################
### fit_routine_plan manages fit routines for an ensemble
###############################################################################

class fit_routine_plan(lfu.plan):

    def __init__(self,*args,**kwargs):
        self._default('name','fit routine plan',**kwargs)
        self._default('routines',[],**kwargs)

        self._default('selected_routine',None,**kwargs)
        self._default('selected_routine_label',None,**kwargs)

        self._default('show_progress_plots',True,**kwargs)

        use = lset.get_setting('fitting')
        self._default('use_plan',use,**kwargs)
        lfu.plan.__init__(self,*args,**kwargs)

    '''#
    def __call__(self, *args, **kwargs):
        if self.show_progress_plots:
            if self.parent.multithread_gui:
                try: app = lgb.QtGui.QApplication(sys.argv)
                except RuntimeError: pass#  this should not be so silent!
            else: self.show_progress_plots = False
        return self._enact(*args,**kwargs)
    '''#

    def _enact(self,*args,**kwargs):
        for routine in self.routines:
            stime = time.time()
            routine._initialize(*args,**kwargs)
            routine._run(*args,**kwargs)
            routine._finalize(*args,**kwargs)
            rtime = str(time.time() - stime)
            print 'completed fit routine',routine.name,'in',rtime,'seconds'
        return args[1]

    def _data(self):
        dpool = dba.batch_node()
        [dpool._add_child(f.data) for f in self.routines]
        return dpool

    # add new fitting routine
    def _add_routine(self,new = None):
        if new is None:new = fab.routine(parent = self)
        if new is None:return
        new.parent = self

        if hasattr(self.parent,'run_params'):
            ops = self.parent.run_params['output_plans']
            ops[new.name+' output'] = new.output

        self.routines.append(new)
        self.children.append(new)
        self.parent.module._rewidget(True)
        self._rewidget(True)

    def _remove_routine(self,select = None):
        if select is None:select = self._selected()
        if select:
            self.routines.remove(select)
            self.children.remove(select)
            if hasattr(self.parent,'run_params'):
                ops = self.parent.run_params['output_plans']
                del ops[select.name+' output']
        self._rewidget(True)

    def _move_routine_up(self, *args, **kwargs):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                        select.label, self.routines)
            self.routines.pop(select_dex)
            self.routines.insert(select_dex - 1, select)
            self._rewidget_routines()

    def _move_routine_down(self, *args, **kwargs):
        select = self._selected()
        if select:
            select_dex = lfu.grab_mobj_dex_by_name(
                        select.label, self.routines)
            self.routines.pop(select_dex)
            self.routines.insert(select_dex + 1, select)
            self._rewidget_routines()

    def _rewidget_routines(self,rewidg = True):
        [rout._rewidget(rewidg) for rout in self.routines]

    def _selected(self):
        key = 'routine_selector'
        if not hasattr(self, key):
            print 'no selector'; return

        try:
            select = self.__dict__[key][
                self.__dict__[key][0].currentIndex()]
            return select

        except IndexError:
            print 'no routine selected'; return

    def _widget(self,*args,**kwargs):
        window = args[0]
        self._sanitize(*args,**kwargs)

        try:select_label = self.selected_routine.label
        except AttributeError:select_label = None

        self.widg_templates.append(
            lgm.interface_template_gui(
                layout = 'grid', 
                widg_positions = [(0,0),(0,2),(1,2),(2,2),(3,2),(4,2)], 
                widg_spans = [(3,2),None,None,None,None,None], 
                grid_spacing = 10, 
                widgets = ['mobj_catalog','button_set'], 
                verbosities = [1,1], 
                instances = [[self.routines,self],None], 
                keys = [[None,'selected_routine_label'],None], 
                handles = [(self,'routine_selector'),None], 
                labels = [None,
                    ['Add Fit Routine','Remove Fit Routine', 
                    'Move Up In Hierarchy','Move Down In Hierarchy']],
                initials = [[select_label],None], 
                bindings = [None,[
                    lgb.create_reset_widgets_wrapper(
                        window,self._add_routine),
                    lgb.create_reset_widgets_wrapper(
                        window,self._remove_routine),
                    lgb.create_reset_widgets_wrapper(
                        window,self._move_routine_up), 
                    lgb.create_reset_widgets_wrapper(
                        window,self._move_routine_down)]]))
        lfu.plan._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################










