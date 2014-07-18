from time import sleep
from time import clock

from math import *
import numpy as np
from scipy import linalg
from scipy import integrate
from scipy import stats
import matplotlib as mpl
from matplotlib import pyplot as plt
from numpy import linalg as la
from numpy import random as rnd
import random
import pdb

import string as str

from multiprocessing import Pool

import cProfile, pstats, StringIO

#from scipy.stats import gamma


import pstats, cProfile
import libchemicalstring_9WM as lcs

import time

import pickle
	
############################################################################
############################################################################

# change fonts so that PDF's do not export with outlined fonts (bad for editing)
mpl.rcParams['pdf.fonttype'] = 42

# make a Matlab-like environment, where plots are updated on the fly
plt.ion()
plt.show()

############################################################################
############################################################################

def genBatch(SysParm):

	SysString, N, nPool = SysParm
	offset = nPool*N

	DataAll = []
	
	start = time.time()
	for samp in range(N):
		RES = lcs.simulate(SysString, samp+offset)
		data = RES[0]
		labels = RES[1]
		DataAll.append(np.array(RES[0], dtype=np.double))
		timeLeft = (N-samp+1)*((time.time()-start)/(samp+1))
		print samp+offset, ', seconds left =', timeLeft, ', minutes left =', timeLeft/60.0

	return labels, np.array(DataAll)

def runBatch(SysString, N):

	NPool = 8
	nSamp = N/NPool
	pool = Pool(NPool)
	SysParms = []
	for ii in range(NPool):
		SysParms.append((SysString, nSamp, ii))
	RES = pool.map(genBatch, SysParms)
	
	labels = RES[0][0]
	vDataAll = np.concatenate([RES[x][1] for x in range(NPool)], axis=0)
	
	meanData = np.mean(vDataAll, axis=0)
	stdData = np.std(vDataAll, axis=0)

	#pdb.set_trace()

	return labels, meanData, stdData

############################################################################
############################################################################

fileIn = 'models/acidTest2.inp'

SysString = open(fileIn).read()
print '-------------------------------------------------------'
print '-------------------------------------------------------'
print SysString
print '-------------------------------------------------------'
print '-------------------------------------------------------'
SysString = SysString.replace('\n','') + '||'

##########################
##########################

TotSamp = 10000;
labels, meanData, stdData = runBatch(SysString, TotSamp)
print labels

##########################
##########################

t = meanData[labels.index('time')]
iter = meanData[labels.index('iteration')]

x_mean = meanData[labels.index('x')]
y_mean = meanData[labels.index('y')]
z_mean = meanData[labels.index('z')]

##########################
##########################

plt.figure(1)

plt.plot(t, x_mean, 'b')
plt.plot(t, y_mean, 'b')
plt.plot(t, z_mean, 'b')

dizzyData = np.genfromtxt('models/acidTest2_dizzy.csv', delimiter=',')
plt.plot(dizzyData[:,0], dizzyData[:,1], 'r')
plt.plot(dizzyData[:,0], dizzyData[:,2], 'r')
plt.plot(dizzyData[:,0], dizzyData[:,3], 'r')

plt.savefig('acidTest2_compare.pdf')

##########################
##########################

plt.figure(2)

plt.plot(t, x_mean-dizzyData[:,1], 'r')
plt.plot(t, y_mean-dizzyData[:,2], 'r')
plt.plot(t, z_mean-dizzyData[:,3], 'r')

plt.savefig('acidTest2_error.pdf')

##########################
##########################

pdb.set_trace()
#raw_input("Press Enter to continue...")


############################################################################
############################################################################


