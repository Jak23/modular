import modular4.base as mb
import modular4.mcfg as mcfg
import modular4.pspacemap as pmp
import modular4.measurement as eme
import modular4.output as mo
import modular4.mpi as mmpi

import sim_anneal.anneal as sa

import numpy,random,time,os,sys,cPickle,subprocess,stat
import matplotlib.pyplot as plt

import pdb



class ensemble(mb.mobject):
    '''
    ensemble uses a simulation module and an mcfg to execute measurements of simulation data
    it provides support for mpi, allowing multicore simulation potentially on a cluster
    it intelligently minimizes data on disk and in memory to accomplish potentially very large parameter scans 
    it performs measurements of the simulation data, 
        and of other measurements forming a hierarchy as specified in the mcfg file
    after simulation and measurement, it provides output using an instance of modular.moutput
    this object can provide among other forms of output, a plotting window interface for data from ensemble instances
    the data can be stored later and viewed using this interface by using the '--plt' command line option
    '''

    simmodules = {
        'gillespiem' : ('gillespiem4','simmodule'), 
        'dstoolm' : ('dstoolm4','simmodule'), 
            }

    def prepare(self):
        '''
        import simulation module, establish self.home directory, and load available measurements
        '''
        if self.rgenseed is None:
            self.rgenseed = random.getrandbits(100)
        self.rgen.seed(self.rgenseed+mmpi.rank())
        if not self.module in self.simmodules:
            mb.log(5,'unknown simulation module!',self.module)
            raise ValueError
        top,smod = self.simmodules[self.module]
        self.simmodule = __import__(top).__dict__[smod]
        self.home = os.path.join(os.getcwd(),self.name)
        if mmpi.root() and not os.path.exists(self.home):
            os.makedirs(self.home)
        mb.load_measurements(eme.parsers,eme.measurement)

    def initialize_measurements(self):
        '''
        prepare measurement and data objects for post simulation measurements
        '''
        z,nz = [],[]
        for mx in range(len(self.measurements)):
            m = self.measurements[mx]
            m._eindex = mx
            if 0 in m.input_sources:
                m.set_targets(self.targets,self.pspace)
                z.append(m)
            else:
                m.set_targets(m.seek_targets(self.measurements),self.pspace)
                nz.append(m)
        self.zeroth,self.nonzeroth = z,nz
        self.zerothdata = [(z[x]._eindex,[],{}) for x in range(len(z))]
        self.nonzerothdata = [(nz[x]._eindex,[],{}) for x in range(len(nz))]

    def set_targets(self,targets):
        '''
        utility method for modifying self.targets
        '''
        for x in range(len(self.targets)):self.targets.pop(0)
        for t in targets:self.targets.append(t)
        return self

    def set_annealer(self,fd,**kws):
        '''
        set up an annealer instance for data fitting
        '''
        x = numpy.linspace(0,self.end,(self.end/self.capture)+1)
        d = fd[0] # hack to select first trajectory only
        newx,newx = mb.linterp(d[0],d[0],x)
        y = numpy.zeros((d.shape[0],newx.size),dtype = numpy.float)
        y[0,:] = newx[:]
        if d.shape[0] > 1:
            for j in range(1,d.shape[0]):
                newx,newy = mb.linterp(d[0],d[j],x)
                y[j,:] = newy[:]
        btx = -1
        for v in x:
            if v > newx.min():break
            else:btx += 1
        ttx = 0
        for v in x:
            if v > newx.max():break
            else:ttx += 1
        simf = self.simmodule.overrides['simulate']
        def f(x,*p):
            px = self.pspacemap.new_location(p)
            self.pspacemap.set_location(px)
            sr = self.run_location(px,simf)
            # hack to return 1st trajectory only for now...
            return sr[0,:,btx:ttx]
        i = self.pspace.current[:]
        b = self.pspace.bounds[:]
        w = numpy.exp((-3.0/newx[-1])*newx)
        w = numpy.array(tuple(w for t in self.targets))
        kws['weights'] = w
        self.anlr = sa.annealer(f,newx,y,i,b,**kws)
        if mmpi.size() > 1 and mmpi.root():
            mmpi.broadcast(['newfitdata',fd,kws])
        return self.anlr

    def find_extract_measurement(self):
        '''
        return the first index of a zeroth order extraction measurement,
          if there is one for the ensemble; else return None
        '''
        for zx in range(len(self.zeroth)):
            if self.zeroth[zx].tag == 'extract':
                return zx

    def batch_scheme(self):
        '''
        return the number of trajectories for a batch call to execute
        '''
        if self.batchsize is None:tc = self.pspacemap.trajcount
        else:tc = min(self.batchsize,self.pspacemap.trajcount)
        return tc

    def __init__(self,*ags,**kws):
        '''
        ensemble class constructor (all inputs are keywords):
        param name : string to identify with this ensemble object
        param module : string to identify which simulation module this ensemble should use
        '''
        self._def('name','ensemble',**kws)
        self._def('module','gillespiem',**kws)
        self._def('simmodule',None,**kws)
        self._def('mcfgfile',None,**kws)
        self._def('pspacemap',[],**kws)
        self._def('targets',[],**kws)
        self._def('measurements',[],**kws)
        self._def('outputs',[],**kws)
        self._def('capture',None,**kws)
        self._def('end',None,**kws)
        self._def('rgenseed',None,**kws)
        self._def('batchsize',None,**kws)
        self._def('serialwork',False,**kws)
        self._def('annealcount',20,**kws)
        self._def('processcount',8,**kws)
        self._def('datascheme','raw',**kws)
        self._def('perform_installation',mmpi.root(),**kws)
        self._def('rgen',random.Random(),**kws)
        self.prepare()

    def parse_mcfg(self,mcfgfile = None,**minput):
        '''
        parse an mcfg file and prepare the ensemble for simulation
        '''
        if not mcfgfile is None:self.mcfgfile = mcfgfile
        if hasattr(self.simmodule,'parsers'):
            module_parsers = self.simmodule.parsers
        else:module_parsers = {}
        mcfg.measurement_parsers = eme.parsers
        einput = mcfg.parse(self.mcfgfile,module_parsers,**minput)
        if 'ensemble' in einput:
            for k,v in einput['ensemble']:
                if k == 'batchsize':self.batchsize = int(v)
                elif k == 'serialwork':self.serialwork = bool(v)
                elif k == 'processcount':self.processcount = int(v)
                else:self.__setattr__(k,str(v))
        if 'targets' in einput:self.set_targets(einput['targets'])
        if 'measurements' in einput:self.measurements = einput['measurements']
        if 'outputs' in einput:self.outputs = einput['outputs']
        if 'capture' in einput:self.capture = einput['capture']
        if 'end' in einput:self.end = einput['end']
        if 'parameterspace' in einput:
            pspace,trajectory,trajcount = einput['parameterspace']
            captcount = int(self.end / self.capture) + 1
            self.pspace = pspace
            pmpags = (pspace,trajectory,trajcount,captcount,self.targets)
            self.pspacemap = pmp.pspacemap(*pmpags)
        self.initialize_measurements()
        if mmpi.size() > 1:self.datascheme = 'none'
        self.pspacemap.prepare(self.datascheme)
        self.simparameters = {}
        for mp in module_parsers:
            if mp in einput:self.simparameters[mp] = einput[mp]
            else:self.simparameters[mp] = ()
        return self

    def output(self,skipe = False):
        '''
        generate output for the simulation data and measurement results
        '''
        try:
            import modular4.qtgui as mg
            mg.init_figure()
        except ImportError:mb.log(5,'could not import gui...')
        result = []
        for ox in range(len(self.outputs)):
            o = self.outputs[ox]
            if ox == 0:
                if skipe:continue
                if mmpi.size() > 1:
                    mb.log(5,'cannot access simulation data from a pspace scan while using mpi...')
                    continue
                else:
                    t,n = self.targets[:],None
                    d = self.pspacemap.get_data(t,n)
            elif self.measurements:
                m = self.measurements[ox-1]
                t = m.targets[:]
                if m in self.zeroth:
                    for d in self.zerothdata:
                        if d[0] == m._eindex:break
                elif m in self.nonzeroth:
                    for d in self.nonzerothdata:
                        if d[0] == m._eindex:break
                else:raise ValueError
            result.append(mo.output(o,d,t,home = self.home))
        return result

    def measure_data_zeroth(self,goalindex,
            precalced = None,returnonly = False,locd = None):
        '''
        perform measurements which depend only on the simulation data
        '''
        pmp = self.pspacemap
        if precalced is None and locd is None:locd = pmp.data[goalindex]
        locp,loct = pmp.goal[goalindex],self.targets
        nzds = []
        for mx in range(len(self.zeroth)):
            m = self.zeroth[mx]
            zd = self.zerothdata[mx][1]
            for x in range(goalindex+1-len(zd)):zd.append([])
            if precalced:nzd = precalced[mx]
            else:nzd = m(locd,loct,locp)
            if returnonly:nzds.append(nzd)
            else:zd[goalindex].append(nzd)
        return nzds

    def measure_data_nonzeroth(self,**kws):
        '''
        perform measurements which depend on other measurements only
        '''
        zd,nzd = self.zerothdata,self.nonzerothdata
        zm,nzm = self.zeroth,self.nonzeroth
        gl,axs = self.pspacemap.goal,self.pspace.axes
        for mx in range(len(nzm)):
            m = nzm[mx]
            for ishp in m.input_shapes:
                if ishp == 'parameterspace':
                    mms = tuple(self.measurements[i-1] for i in m.input_sources)
                    zero = tuple(zd[zx] for zx in range(len(zd)) if zm[zx] in mms)
                    nzero = tuple(nzd[zx] for zx in range(len(nzd)) if nzm[zx] in mms)
                    nonzmeasurement = m(zero+nzero,axs,gl,**kws)
                    self.nonzerothdata[mx][1].append(nonzmeasurement)

    def run_location(self,px,simf):
        '''
        generate and return some simulation data associated with a location in parameter space
        '''
        targcnt,captcnt,p = self.pspacemap.set_location(px)
        trajcnt = self.batch_scheme()
        d = numpy.zeros((trajcnt,targcnt,captcnt),dtype = numpy.float)
        for x in range(trajcnt):
            r = self.rgen.getrandbits(100)
            d[x] = simf(r,*p)
        if mmpi.root():
            mstr = 'rank %i ran %i batch at location: %i'
            mb.log(5,mstr % (mmpi.rank(),trajcnt,px))
        return d

    def run(self):
        '''
        main entry point to run an ensemble
        '''
        if mmpi.root():
            if mmpi.size() == 1:
                if self.pspace._purpose == '<fit>':
                    r = self.run_fitting()
                elif self.pspace._purpose == '<map>':
                    if self.serialwork:
                        r = self.run_dispatch_serial()
                    else:r = self.run_basic()
            else:
                if self.pspace._purpose == '<fit>':
                    r = self.run_fitting_dispatch()
                elif self.pspace._purpose == '<map>':
                    r = self.run_dispatch()
        else:r = self.run_listen()
        return r

    def run_basic(self):
        '''
        run simulations using a single core
        '''
        simf = self.simmodule.overrides['prepare'](self)
        for px in range(len(self.pspacemap.goal)):
            pdata = self.run_location(px,simf)
            self.pspacemap.add_data(pdata)
            self.measure_data_zeroth(px)
        self.measure_data_nonzeroth()
        return self.output()

    def run_fitting(self):
        '''
        perform simulated annealing using simulation data
        param d : data to fit to; must overlap with domain given by mcfg
        '''
        result,error = self.anlr.anneal()
        px = self.pspacemap.new_location(result)
        self.pspacemap.set_location(px)
        simf = self.simmodule.overrides['simulate']
        pdata = self.run_location(px,simf)
        exx = self.find_extract_measurement()
        if not exx is None:
            zdata = self.measure_data_zeroth(px,returnonly = True,locd = pdata)
            zdata[exx][2]['extra_trajectory'] = []
            for yd,t in zip(self.anlr.y,self.targets):
                if t == 'time':continue
                zdata[exx][2]['extra_trajectory'].append(
                    ((self.anlr.y[0],yd),{'label':t+'-data'}))
            self.measure_data_zeroth(px,precalced = zdata)
        return result,error

    def run_fitting_dispatch(self):
        '''
        act as a dispatcher for a fitting routine that leverages mpi
        '''
        def issue():
            ng,p = todo.pop(-1),free.pop(0)
            mmpi.broadcast(['execfit',ng],p)
            occp.append(p)
            issd.append(ng)

        def ameas(gs):
            todo.extend(list(gs))
            gcnt = len(todo)
            ms,bg = self.anlr.m,None
            mcnt = 0
            while mcnt < gcnt:
                while free and todo:issue()
                while occp:
                    r = mmpi.passrecv()
                    if not r is None and int(r) in occp:
                        free.append(r);occp.remove(r)
                        rg,rm = mmpi.pollrecv(r)
                        issd.remove(rg)
                        if rm < ms:
                            ms = rm
                            bg = rg
                            for x in range(len(todo)):todo.pop(0)
                            return ms,bg
                        mcnt += 1
                        break
                    #elif todo:break
                    elif len(issd) <= maxissue:return ms,bg
            return ms,bg

        def fin():
            for j in range(len(todo)):todo.pop(0)
            for j in range(len(issd)):issd.pop(0)
            while occp:
                r = mmpi.passrecv()
                if not r is None and int(r) in occp:
                    free.append(r);occp.remove(r)
                    rg,rm = mmpi.pollrecv(r)
            
        maxissue = int(mmpi.size()*1.0)
        free,occp,todo,issd = list(range(1,mmpi.size())),[],[],[]

        self.anlr.measure = ameas
        self.anlr.finish = fin
        result,error = self.anlr.anneal_auto(self.annealcount)
        #result,error = self.anlr.anneal()
        exx = self.find_extract_measurement()
        if not exx is None:
            px = self.pspacemap.new_location(result)
            self.pspacemap.set_location(px)
            simf = self.simmodule.overrides['simulate']
            pdata = self.run_location(px,simf)
            zdata = self.measure_data_zeroth(px,returnonly = True,locd = pdata)
            zdata[exx][2]['extra_trajectory'] = []
            for yd,t in zip(self.anlr.y,self.targets):
                if t == 'time':continue
                zdata[exx][2]['extra_trajectory'].append((
                    (self.anlr.y[0],yd),
                    {'color':'g','label':t+'-data','linestyle':'--'}))
            self.measure_data_zeroth(px,precalced = zdata)
        return result,error

    def run_dispatch(self):
        '''
        run a dispatcher process that issues work to nonroot processes running self.run_listen
        '''
        mb.log(5,'dispatch beginning: %i' % mmpi.rank())
        simf = self.simmodule.overrides['prepare'](self)
        hosts = mmpi.hosts()
        for h in hosts:
            mb.log(5,'hostlookup: %s : %s' % (h,str(hosts[h])))
            if not h == 'root' and not h == mmpi.host():
                mmpi.broadcast('prom',hosts[h][0])
        mmpi.broadcast('prep')
        bsize = self.batch_scheme()
        wholesome = bsize == self.pspacemap.trajcount
        batch_cnt = self.pspacemap.trajcount/bsize
        many_batch = [batch_cnt for x in range(len(self.pspacemap.goal))]
        done_batch = [0 for x in range(len(self.pspacemap.goal))]
        pool_batch = [None for x in range(len(self.pspacemap.goal))]
        todo,done = [x for x in range(len(self.pspacemap.goal))],[]
        free,occp = [x for x in range(mmpi.size())],[]
        free.remove(mmpi.rank())
        while len(done) < len(self.pspacemap.goal):
            time.sleep(0.01)
            if todo and free:
                p = free.pop(0)
                many_batch[todo[0]] -= 1
                if many_batch[todo[0]] == 0:w = todo.pop(0)
                else:w = todo[0]
                mmpi.broadcast(['exec',w],p)
                occp.append(p)
            if occp:
                r = mmpi.passrecv()
                if not r is None and int(r) in occp:
                    mb.log(5,'result from worker: %i' % r)
                    px,pdata = mmpi.pollrecv(r)
                    free.append(r);occp.remove(r)
                    done_batch[px] += 1
                    if done_batch[px] == batch_cnt:done.append(px)
                    targcnt,captcnt,p = self.pspacemap.set_location(px)
                    if wholesome:self.measure_data_zeroth(px,precalced = pdata)
                    else:
                        if pool_batch[px] is None:pool_batch[px] = []
                        pool_batch[px].append(pdata)
                        if px in done:
                            pdata = pool_batch[px]
                            bshpe = (self.pspacemap.trajcount,targcnt,captcnt)
                            bdata = numpy.zeros(bshpe,dtype = numpy.float)
                            for bx in range(batch_cnt):
                                bdata[bx*bsize:(bx+1)*bsize] = pdata[bx]
                            self.measure_data_zeroth(px,locd = bdata)
                            pool_batch[px] = None
        self.measure_data_nonzeroth()
        mmpi.broadcast('halt')
        mb.log(5,'dispatch halting: %i' % mmpi.rank())
        return self.output()

    def run_listen(self):
        '''
        run a listener process that performs work for a root running self.run_distpatch
        '''
        mb.log(5,'listener beginning: %i' % mmpi.rank())
        wholesome = self.batch_scheme() == self.pspacemap.trajcount
        m = mmpi.pollrecv(0)
        while True:
            if m == 'halt':break
            elif m == 'host':mmpi.broadcast(mmpi.host(),0)
            elif m == 'prom':self.perform_installation = False
            elif m == 'prep':simf = self.simmodule.overrides['prepare'](self)
            elif m == 'exec':
                j = mmpi.pollrecv(0)
                if wholesome:
                    r = self.run_location(j,simf)
                    r = (j,self.measure_data_zeroth(j,returnonly = True,locd = r))
                else:r = (j,self.run_location(j,simf))
                mmpi.broadcast(mmpi.rank(),0)
                mmpi.broadcast(r,0)
                mb.log(5,'listener sent result: %s' % str(j))
            elif m == 'execfit':
                j = mmpi.pollrecv(0)
                a = self.anlr
                fm = a.metric(a.f(a.x,*j),a.y,a.weights)
                mmpi.broadcast(mmpi.rank(),0)
                mmpi.broadcast((j,fm),0)
            elif m == 'newfitdata':
                newy = mmpi.pollrecv(0)
                skws = mmpi.pollrecv(0)
                self.set_annealer(newy,**skws)
            else:mb.log(5,'listener received unknown message: %s' % m)
            m = mmpi.pollrecv(0)
        mb.log(5,'listener halting: %i' % mmpi.rank())

    def run_dispatch_serial(self):
        '''
        run a serial submission dispatcher process that issues work to
        disconnect processes and waits for their results to appear
        '''
        mb.log(5,'serial dispatch beginning: %i' % mmpi.rank())
        simf = self.simmodule.overrides['prepare'](self)
        dfdir = os.path.join(self.home,'tempdata')
        if not os.path.exists(dfdir):os.makedirs(dfdir)
        scriptfile = os.path.join(dfdir,'tempscript.sh')
        dfbase = '.'.join(['pspacedata','$','pkl'])
        dfs = []
        for x in range(len(self.pspacemap.goal)):
            dfname = dfbase.replace('$',str(x))
            dfs.append(os.path.join(dfdir,dfname))
        unstarted,ready,complete = dfs[:],[],[]

        def new(f):
            if not f.endswith('.pkl'):return False
            elif not f in dfs:return False
            elif f in complete:return False
            else:return True

        processes = 0
        while len(complete) < len(dfs):
            if unstarted and processes < self.processcount:
                df = unstarted.pop(0)
                self.run_serial_process(dfs.index(df),df,scriptfile)
                processes += 1
            elif ready:
                for df in ready:
                    with open(df,'rb') as h:px,pr = cPickle.load(h)
                    self.pspacemap.set_location(px)
                    self.measure_data_zeroth(px,precalced = pr)
                    complete.append(df)
                for x in range(len(ready)):ready.pop(0)
            else:
                newfiles = [os.path.join(dfdir,f) for f in os.listdir(dfdir)]
                for nf in newfiles:
                    if new(nf):
                        processes -= 1
                        ready.append(nf)
                time.sleep(0.01)
        self.measure_data_nonzeroth()
        mb.log(5,'serial dispatch finished: %i' % mmpi.rank())
        return self.output()

    def run_serial_process(self,locx,dfile,scriptfile):
        '''
        deploy a process which executes a serial job using self.run_serial
          this process saves the results at the provided data filename
        '''
        ags = [sys.executable,'-m','modular4.mrun',self.mcfgfile,'--serial',str(locx),dfile]
        locscript = scriptfile.replace('.sh','.'+str(locx)+'.sh')
        with open(locscript,'w') as h:h.write(' '.join(ags))
        st = os.stat(locscript)
        os.chmod(locscript,st.st_mode | stat.S_IEXEC)
        #p = subprocess.Popen(['qsub',scriptfile])
        p = subprocess.Popen(['bash',locscript])

    def run_serial(self,px,dfile):
        '''
        execute the work of pspace location px 
        and save the zeroth measurements in dfile
        '''
        self.perform_installation = False
        simf = self.simmodule.overrides['prepare'](self)
        sr = self.run_location(px,simf)
        pr = (px,self.measure_data_zeroth(px,returnonly = True,locd = sr))
        with open(dfile,'wb') as h:cPickle.dump(pr,h)






