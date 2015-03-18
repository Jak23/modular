import modular_core.fundamental as lfu
import modular_core.fitting.routine_abstract as fab
import modular_core.fitting.metrics as mts
import modular_core.data.batch_target as dba
import modular_core.io.pkl as pk

import pdb,os
import scipy.interpolate as sp
import matplotlib.pyplot as plt
import numpy as np

###############################################################################
###
###############################################################################

def interpolate(wrongx,wrongy,rightx,kind = 'linear'):
    interpolation = sp.interp1d(wrongx,wrongy,bounds_error = False,kind = kind)
    righty = interpolation(rightx)
    return righty

class annealing(fab.routine_abstract):

    def _capture_measurements(self,mes):
        bestflags = []
        for mx in range(self.metric_count):
            me = mes[mx]
            metme = self.metric_measurements[mx]
            metme.append(me)
            if me <= min(metme):metbest = True
            else:metbest = False
            bestflags.append(metbest)
        if bestflags.count(True) > 0:
            print 'found best!'
            self.best = True

    def _fitter(self,measures,noisey = 0.1):
        if not self.metric_measurements[0]:fitter = True
        else:
            last = [m[-1] for m in self.metric_measurements]
            better = [(l-m) > (-1.0*noisey*m) for l,m in zip(last,measures)]
            mthrsh = int(self.metric_count/2)
            if better.count(True) >= mthrsh:fitter = True
            else:fitter = False
        if fitter:self._capture_measurements(measures)
        return fitter

    # consider a measurement, undo or keep step?
    def _accept_step(self,information,ran):
        if self.iteration == 0:
            self.best = True
            return True
        else:self.best = False
        if not ran:return False
        runintp = dba.batch_node(
            dshape = self.input_data.dshape,
            targets = self.input_data.targets)
        rundata = information.data[0]
        inpdata = self.input_data.data
        runintp.data[0] = inpdata[0]
        for dx in range(1,rundata.shape[0]):
            rdat = rundata[dx]
            runintp.data[dx] = interpolate(rundata[0],rdat,inpdata[0])

        temp_measurements = []
        for mdx in range(self.metric_count):
            met = self.metrics[mdx]
            m = met._measure(self.input_data,runintp)
            temp_measurements.append(m)

        runintp._stow(v = False)
        fitter = self._fitter(temp_measurements)
        return fitter

    def _open_data(self):

        dpath = os.path.join(os.getcwd(),'mm_fit_input.0.pkl')
        idata = pk.load_pkl_object(dpath)

        ### THIS IS CURRENTLY UNUSED.... IT PROBABLY SHOULD BE USED....
        ptargets = self.parent.parent.simulation_plan.plot_targets
        itargets = [d.name for d in idata.data]
        aliases = {}
        for ak,rk in zip(itargets,ptargets):
            aliases[ak] = rk
        ### THIS IS CURRENTLY UNUSED.... IT PROBABLY SHOULD BE USED....

        dshape = (len(idata.data),len(idata.data[0].data))
        targets = [d.name for d in idata.data]
        idatanode = dba.batch_node(dshape = dshape,targets = targets)
        for fdx in range(dshape[0]):
            idatanode.data[fdx,:] = idata.data[fdx].data[:]
        self.input_data = idatanode

    def __init__(self,*args,**kwargs):
        self._default('name','an annealer',**kwargs)
        self._default('max_iteration',10000.0,**kwargs)
        self._default('max_temperature',1000.0,**kwargs)
        #self.metrics = [mts.difference()]
        self.metrics = [mts.difference(),mts.derivative1()]
        #self.metrics = [mts.difference(),mts.derivative1(),mts.derivative2()]
        self.metric_count = len(self.metrics)
        fab.routine_abstract.__init__(self,*args,**kwargs)

    def _initialize(self,*args,**kwargs):
        self._open_data()
        self.metric_measurements = [[] for m in self.metrics]

        finali = int(self.max_iteration)
        mtemp = self.max_temperature
        lam = -1.0 * np.log(mtemp)/finali
        cooling_domain = np.array(range(finali))
        self.cooling = np.exp(lam*cooling_domain)

        fab.routine_abstract._initialize(self,*args,**kwargs)
        self.max_temperature = mtemp

    def _movement_factor(self):
        self.temperature = self.cooling[self.iteration]
        return self.temperature/self.max_temperature

    def _target_settables(self,*args,**kwargs):
        capture_targetable = self._targetables(*args,**kwargs)
        self.target_list = capture_targetable[:]
        self.capture_targets = self.target_list 
        fab.routine_abstract._target_settables(self,*args,**kwargs)

    def _widget(self,*args,**kwargs):
        self._sanitize(*args,**kwargs)
        self._target_settables(*args,**kwargs)
        capture_targetable = self._targetables(*args,**kwargs)
        fab.routine_abstract._widget(self,*args,from_sub = True)

###############################################################################
###############################################################################

# return valid **kwargs for annealing based on msplit(line)
def parse_line(split,ensem,procs,routs):
    eargs = {
        'name':split[0],
        'variety':split[1],
            }
    return eargs

###############################################################################

if __name__ == 'modular_core.fitting.annealing':
    lfu.check_gui_pack()
    lgb = lfu.gui_pack.lgb
    lgm = lfu.gui_pack.lgm
    lgd = lfu.gui_pack.lgd
    fab.routine_types['annealing'] = (annealing,parse_line)

###############################################################################










