#!/usr/bin/env python
import modular4.base as mb
import modular4.ensemble as me
import modular4.output as mo
import modular4.mpi as mmpi

import argparse,sys,os,time,numpy,logging,multiprocessing

import pdb



def run_pklplotter_file(p,f):
    st = time.time()
    mb.log(5,'begin loadpkl',f,mb.clock(st))
    o = mo.loadpkl(os.path.join(p,f))
    o.modes = ['plt']
    et = time.time()
    mb.log(5,'end loadpkl',f,mb.clock(et))
    mb.log(5,'ran loadpkl in %f seconds' % numpy.round(et-st,3),f)
    o()

def run_pklplotter(p):
    if mmpi.root():
        import modular4.qtgui as mg
        mg.init_figure()
        proc = multiprocessing.Process
        if not os.path.exists(p):p = os.getcwd()
        fs = os.listdir(p)
        oprocs = []
        for f in fs:
            if f.endswith('.pkl'):
                #run_pklplotter_file(p,f)
                pltprocess = proc(target = run_pklplotter_file,args = (p,f))
                pltprocess.start()
                oprocs.append(pltprocess)
        for op in oprocs:op.join()

def run_slave(mcfg):
    s = time.time()
    try:locx,dfile = int(sys.argv[3]),sys.argv[4]
    except:
        mb.log(5,'serial submission called with invalid inputs!')
        raise ValueError
    r = me.ensemble(datascheme = 'none').parse_mcfg(mcfg).run_serial(locx,dfile)
    t = time.time()-s

def run_mcfg(mcfg,name,modu):
    st = time.time()
    if mmpi.root():mb.log(5,'begin run',mb.clock(st))
    r = me.ensemble(name = name,module = modu).parse_mcfg(mcfg).run()
    et = time.time()
    if mmpi.root():
        mb.log(5,'end mcfg run: %s' % mb.clock(et))
        mb.log(5,'ran mcfg in %f seconds' % numpy.round(et-st,3))
        return tuple(o() for o in r)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mcfg',required = False,type = str,default = '',help = 'path to mcfg file')
    parser.add_argument('--name',required = False,type = str,default = 'ensemble',help = 'ensemble name')
    parser.add_argument('--mod', required = False,type = str,default = 'gillespiem',help = 'simulation module')
    parser.add_argument('--dir', required = False,type = str,default = os.getcwd(),help = 'default directory used for plotting')
    parser.add_argument('--plt', required = False,action = "store_true",default = False,help = 'perform plotting')
    parser.add_argument('--np',  required = False,type = int,default = 1,help = 'number of processes intended for use')
    parser.add_argument('--mpi', required = False,type = str,default = '',help = 'hostfile for use with mpi')
    parser.add_argument('--slave',action = "store_true",default = False,help = '')
    options = parser.parse_args()
    if options.plt:run_pklplotter(options.dir)
    elif options.mcfg:
        mcfg = os.path.join(os.getcwd(),options.mcfg)
        if not os.path.isfile(mcfg):
            mb.log(5,'COULD NOT LOCATE MCFG: %s' % mcfg)
        else:
            if options.slave:run_slave(mcfg,options.name,options.mod)
            else:run_mcfg(mcfg,options.name,options.mod)
    else:mb.log(5,'NO MCFG PROVIDED')





