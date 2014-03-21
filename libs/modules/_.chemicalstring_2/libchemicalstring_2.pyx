#imports
cimport cython

from libc.math cimport log as log
#from libc.math cimport sin as sinc
#from libc.math cimport cos as cosc
#from math import log as log
from math import sin as sin
from math import cos as cos
import numpy as np
from numpy import random as rnd
import re
import random

pwm_square = None

#Will's random number generator
cdef class GENRAND:

	cdef long inow
	cdef long SIZE
	cdef double [:] randbuf

	def __init__(self, seed=1000):
		rnd.seed(seed)
		self.inow = 0
		self.SIZE = 100000
		self.randbuf = rnd.random(size = self.SIZE)

	cdef double gen(self):
		if (self.inow<self.SIZE):
			self.inow = self.inow+1
			#print self.randbuf[self.inow-1]
			return self.randbuf[self.inow-1]
		else:
			#print "buffer reset"
			self.inow = 0
			self.randbuf = rnd.random(size = self.SIZE)
			#print self.randbuf[self.inow]
			return self.randbuf[self.inow]

cdef class pwm_sq:

	cdef double period
	cdef double phase
	cdef double pwm_time_up
	cdef str domain
	cdef int dex0
	cdef int dex1

	#only gets initialized once, using paramters of first pwm_square found
	def __init__(self, *args, **kwargs):
		global pwm_square

		encoded = args[0]
		cnts = args[1]
		targs = args[2]

		dex0 = encoded.find('pwm_square(') + len('pwm_square(')
		dex1 = encoded[dex0:].find(')') + dex0
		params_str = encoded[dex0:dex1].split(':')
		params_val = []
		for par in params_str[:-1]:
			dex = targs.index(par)
			params_val.append(cnts[dex])

		self.period = params_val[0]
		self.phase = params_val[1]
		self.pwm_time_up = params_val[2]
		self.domain = str(params_str[-1])

		pwm_square = self.__call__

	#all calls will look the same
	def get_encoded(self, encoded):
		dex0 = encoded.find('pwm_square(') + len('pwm_square(')
		dex1 = encoded[dex0:].find(')') + dex0
		return encoded.replace(encoded[dex0:dex1], self.domain)

	def __call__(self, t):
		t_w = (t + self.phase) % self.period
		#print t, t_w, self.period, t_w/self.period, self.pwm_time_up, t_w/self.period > self.pwm_time_up
		if t_w/self.period > self.pwm_time_up: return 0.0
		return 1.0


#bulk of preprocessing is here
#propensities which depend on a function should appear on
# every reactions' affected list?
@cython.boundscheck(False) # turn of bounds-checking for entire function
@cython.cdivision(False)
def generate_reaction(count_targets, counts, functions, func_names, 
				var_vals, variables, rxn_string, rate_call_group):

	#rate was not a float and some stochiometric coefficient > 1; slowest
	def propensity_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex = 1
		cdef int act_dex = 0
		cdef int cnt
		cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float and all stochiometric coefficients = 1
	def propensity_simple_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		cdef int cnt_dex
		cdef int cnt
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was not a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple_with_rate_call():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef double zero = 0.0
		propensity = counts[cnt_dexes[0]] * rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return zero	#is this faster?

	#rate was not a float and there are no reagents
	def propensity_simplest_with_rate_call():
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity_minimum = 1e-30
		propensity = rate(counts)
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and some stochiometric coefficient > 1
	def propensity():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex = 1
		cdef int act_dex = 0
		cdef int cnt
		cdef int act
		cdef int k
		for agent in reagents:
			cnt = counts[agent[cnt_dex]]
			act = agent[act_dex]
			for k in range(act): population *= cnt - k
			population /= act

		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and all stochiometric coefficients = 1
	def propensity_simple():
		cdef double population = 1.0
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		cdef int cnt_dex
		cdef int cnt
		#list comprehension? probably slower; need to test!
		for cnt_dex in cnt_dexes: population *= counts[cnt_dex]
		propensity = population * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float, there is but one stochiometric
	# coefficient and it is equal to 1
	def propensity_very_simple():
		cdef double propensity = 1.0
		cdef double propensity_minimum = 1e-30
		propensity = counts[cnt_dexes[0]] * rate
		if propensity > propensity_minimum: return propensity
		else: return 0.0

	#rate was a float and there are no reagents
	# this if statement can be preprocessed/configured via lambda function!
	#def propensity_simplest():
	#	cdef double propensity_minimum = 1e-30
	#	cdef double rate
	#	if rate > propensity_minimum: return rate
	#	else: return 0.0

	#if reagents is empty, the reaction is ALWAYS valid
	def validator_constant(): return True

	#if reagents is nonempty, they MUST be checked before reacting
	def validator():
		cdef int dex
		cdef int leng = len(cnt_dexes)
		#can this be a list comprehension / does that help?
		for dex in range(leng):
			if counts[cnt_dexes[dex]] < stochios[dex]: return False

		return True

	def reaction():
		for agent in reagents: counts[agent[1]] -= agent[0]
		for agent in products: counts[agent[1]] += agent[0]

	#this should not be used anymore!
	#def use_rate(double rate):
	#	def rate_(cnts, varis): return rate
	#	return rate_

	def measure_agent(agent):
		nothings = ['nothing', 'null', '']
		if not agent in nothings:
			one = agent.find('(')
			two = agent.find(')')
			amt = int(agent[one + 1:two])
			spec_dex = count_targets.index(agent[two + 1:])
			return (amt, spec_dex)

		else: return (0, count_targets.index('null'))

	split = rxn_string.split('->')
	try:
		rate = float(split[1])
		rate_flag = False

	except ValueError:
		try:
			func_dex = func_names.index(split[1])
			rate = functions[func_dex]
			rate_flag = True

		except ValueError:
			var_dex = variables.index(split[1])
			rate = float(var_vals[var_dex])
			rate_flag = False

	cdef double propensity_minimum = 1e-30
	reagents = [measure_agent(agent) for agent in split[0].split('+')]
	products = [measure_agent(agent) for agent in split[2].split('+')]
	cnt_dexes = [agent[1] for agent in reagents]
	try:
		stochios, cnt_dexes = zip(*[(agent[0], cnt) for agent, cnt 
					in zip(reagents, cnt_dexes) if agent[0] > 0])

	except ValueError: stochios, cnt_dexes = [], []
	if len(cnt_dexes) == 0: has_reagents = False
	elif len(cnt_dexes) == 1 and stochios[0] > 0:
		has_reagents = True; only_one_reagent = True

	else: has_reagents = True; only_one_reagent = False
	if len(stochios) == sum(stochios): single_stochios = True
	rate_call_group.append(rate_flag)
	if not rate_flag:
		if not has_reagents:
			valid = validator_constant
			if rate > propensity_minimum:
				correct_propensity = lambda: rate

			else: correct_propensity = lambda: 0.0

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple

			elif single_stochios: correct_propensity = propensity_simple
			else: correct_propensity = propensity

	else:
		if not has_reagents:
			valid = validator_constant
			correct_propensity = propensity_simplest_with_rate_call

		else:
			valid = validator
			if only_one_reagent and single_stochios:
				correct_propensity = propensity_very_simple_with_rate_call

			elif single_stochios:
				correct_propensity = propensity_simple_with_rate_call

			else: correct_propensity = propensity_with_rate_call

	return correct_propensity, valid, reaction, reagents, products



#return a sequence identical to seq but with no duplicates
cdef uniq(seq):
	seen = {}
	result = []
	for item in seq:
		if item in seen: continue
		seen[item] = 1
		result.append(item)

	return result



#propensity functions are replaced with functions which instead
# update the dependant propensity functions based on reactions
def wrap_propensities(propensity_table, propensities, 
				reagents, products, rate_call_group):

	def generate_wrap(lookup):

		def propensity_wrap():
			cdef int dex
			cdef int sub_dex
			for dex in range(leng):
				sub_dex = lookup[dex]
				propensity_table[sub_dex] = propensities[sub_dex]()

		cdef int leng = len(lookup)
		return propensity_wrap

	#if any reactions propensity depends on say time, it must be appended
	#	to every lookup
	#		alwayses should consist of the indexes of every propensity 
	#			which requires a rate call
	alwayses = [dex for dex in range(len(rate_call_group)) 
								if rate_call_group[dex]]
	propensity_lookups = [[] for prop in propensities]
	for dex in range(len(reagents)):
		current = set([agent[1] for agent in products[dex]])
		for dex2 in range(len(reagents)):
			temporary = set([agent[1] for agent in reagents[dex2]])
			if temporary & current:
				propensity_lookups[dex].append(dex2)

		propensity_lookups[dex].extend(alwayses)

	propensity_lookups = [uniq(lookup) for lookup in propensity_lookups]
	return [generate_wrap(lookup) for lookup in propensity_lookups]



#turn function strings into compiled lambda functions
def generate_functions(functions, count_targets, counts):

	def convert(substr):
		if substr in count_targets:
			return "".join(["counts[", 
				str(count_targets.index(substr)), "]"])

		else: return substr

	def encode(string):
		return ''.join([convert(substr) for substr in string])

	func_names = [fu[:fu.find('=')] for fu in functions]
	encoded = [fu[fu.find('=') + 1:] for fu in functions]
	encoded = ['lambda counts: ' + encode(re.split('(\W)', string)) 
											for string in encoded]
	funcs = [eval(expr) for expr in encoded]
	return func_names, funcs



#various simplified test functions available to make_test
def make_lt_eq(counts, int cnt_dex, double value):
#def make_lt_eq(counts, cnt_dex, value):
	def lt_eq(): return counts[cnt_dex] <= value
	return lt_eq

def make_gt_eq(counts, int cnt_dex, double value):
#def make_gt_eq(counts, cnt_dex, value):
	def gt_eq(): return counts[cnt_dex] >= value
	return gt_eq

def make_lt(counts, int cnt_dex, double value):
#def make_lt(counts, cnt_dex, value):
	def lt(): return counts[cnt_dex] < value
	return lt

def make_gt(counts, int cnt_dex, double value):
#def make_gt(counts, cnt_dex, value):
	def gt(): return counts[cnt_dex] > value
	return gt

def make_increment(counts, data, int cnt_dex, double value):
#def make_increment(counts, data, cnt_dex, value):
	def incre(): return counts[cnt_dex] - data[cnt_dex][-1] >= value
	return incre

def make_asymmetric_increment(counts, data, int dex1, int dex2, double value):
#def make_asymmetric_increment(counts, data, dex1, dex2, value):
	def asym_incre(): return counts[dex1] - data[dex2][-1] >= value
	return asym_incre



#returns a function which checks the specified criterion in string
def make_test(counts, data, count_targets, string):
	eq_rel = ['>' in string, '<' in string, '>=' in string, '<=' in string]
	if eq_rel[3]:
		return make_lt_eq(counts, count_targets.index(string[:string.find('<=')]), 
									float(string[string.find('<=') + 2:]))

	elif eq_rel[2]:
		return make_gt_eq(counts, count_targets.index(string[:string.find('>=')]), 
									float(string[string.find('>=') + 2:]))

	elif eq_rel[1]:
		return make_lt(counts, count_targets.index(string[:string.find('<')]), 
								float(string[string.find('<') + 1:]))

	elif eq_rel[0]:
		return make_gt(counts, count_targets.index(string[:string.find('>')]), 
								float(string[string.find('>') + 1:]))

	elif string.startswith('increment'):
		left = string.find(':') + 1
		right = string.rfind(':')
		incr_target = string[left:right]
		return make_increment(counts, data, 
				count_targets.index(incr_target), 
				float(string[right + 1:]))

	else:
		print 'here is that one bug...'
		print counts, data, count_targets, string



#helper function to break up string representations of the system
cdef inline parse(system_string, int dex, string):
	cdef int new_dex
	new_dex = system_string.find(string)
	return system_string[dex:new_dex], new_dex



#reorder targets so they will match order of data lists
cdef follow_order(targets, count_targets):
	targs = []
	[targs.append(targ) for targ in count_targets if targ in targets]
	return targs



#identifies a relatively huge jump in value in a sequence of values
#used here to identify when time 'explodes' as the propensity of 
# every reaction approaches zero
# - not called if end criteria are met
def find_infinite_tail(sequence, ratio_res = 1.0, min_seq_length = 100):

	def max_of_diff_splits(seq):
		middle = len(seq)/2
		split1 = seq[:middle]
		split2 = seq[middle:]
		return split2, split1

	complete_deltas = [sequence[k] - sequence[k - 1] for k in 
									range(len(sequence))][1:]
	if len(complete_deltas) == 0 or len(sequence) < min_seq_length:
		return 0

	deltas = complete_deltas
	ratio = max(deltas)/min(delt for delt in deltas if delt > 0.0)
	ratio_threshold = ratio/ratio_res	#anticpate magnitude of jump
	while ratio > ratio_threshold:
		split2, split1 = max_of_diff_splits(deltas)
		try: max1 = max(split1); max2 = max(split2)
		except ValueError:
			print 'failed to find that tail!'
			return -1

		if max2/max1 > ratio_threshold: deltas = split2
		else: deltas = split1
		ratio = max(deltas)/min(deltas)

	last_good_dex = complete_deltas.index(deltas[-1])
	return last_good_dex + 1



#indentifies the last data capture before the reactions occur
# incredibly spaced out in time (relative to the majority of the data)
cdef inline validate_data(data, int dex):
	cdef int validex
	validex = find_infinite_tail(data[dex])
	if validex < 100: return len(data[dex]) - 10
	else: return validex



#used to generate functions for capture and end criteria tests
def generate_test(count_targets, data, counts, split):

	#create a function which returns True if all tests return True
	# and False otherwise
	def make_and_condition(tests):

		def and_condition():
			return False not in [test() for test in tests]

		return and_condition

	#only create AND logic wrapper if 2+ tests specified in split
	if len(split) > 1:
		tests = [make_test(counts, 
			data, count_targets, spl) 
					for spl in split]
		return make_and_condition(tests)

	#if only one test specified, return the unwrapped test function
	else: return make_test(counts, data, count_targets, split[0])



#appends the appropriate values of the counts vector
# to the appropriate data lists in the data structure
def generate_capture_function(data, target_dexes, counts):

	def capture():
		values = [counts[dex] for dex in target_dexes]
		[data[dex].append(value) for dex, value in 
						zip(target_dexes, values)]

	return capture



#@cython.boundscheck(False) # turn of bounds-checking for entire function
#@cython.cdivision(False)
cdef inline int pick_reaction(double [:] table, double rand, int leng):
	cdef int dex
	for dex in range(leng):
		if rand < table[dex]:
			return dex



#create a function which updates the current functions' values
def generate_update_functions(count_targets, counts, 
							functions, func_names):

	def dummy(): pass
	def update_function():
		func_dex = count_targets.index(func_names[0])
		for dex in range(func_dex, len(counts)):
			counts[dex] = functions[dex - func_dex](counts)

	if not func_names: return dummy
	else: return update_function



#temporarily here to use debug_string.txt
import os

@cython.boundscheck(False) #no IndexErrors can be allowed to occur
@cython.cdivision(False)
#simulates and returns data of one trajectory of a system
def simulate(system_string = '<species>Substrate:10000,Enzyme:5000,ES_Complex:0,Product:0<variables>k:0.5<functions>ratio=Substrate/(Enzyme+k)<reactions>(1)Substrate+(1)Enzyme->1.0->(1)ES_Complex,(1)ES_Complex->0.01->(1)Substrate+(1)Enzyme,(1)ES_Complex->800.0->(1)Enzyme+(1)Product<end>iteration>=10000<capture>increment:time:0.00002<targets>ES_Complex,Product,iteration,time,fixed_time||'):

	#some code to print a system_string to a txt file... to be certain the system_strings I give you work
	path = os.path.join(os.getcwd(), 'libs', 'modules', 'debug_string.txt')
	with open(path, 'w') as handle: handle.write(system_string)
	#


	#initializations, mostly used for cython
	cdef int iteration = 0
	cdef int rxn_dex = 0
	cdef double time = 0.0
	cdef double fixed_time = 0.0
	cdef double fixed_delt = 1.0
	cdef double fixed_time_step = 0.0
	cdef double time_step = 0.0
	cdef double last_time = 0.0
	cdef double last_fixed_time = 0.0
	cdef double propensity_total
	cdef double propensity_total_inv
	cdef double rand_rxn
	cdef double rand_time
	cdef int prop_dex
	cdef int propensity_count
	cdef int next_dex
	cdef int dex
	cdef int fixed_steps
	cdef int fixed_update


	#break the system_string up for processing
	species, next_dex = parse(system_string, 0, '<variables>')
	variables, next_dex = parse(system_string, next_dex, '<functions>')
	functions, next_dex = parse(system_string, next_dex, '<reactions>')
	rxns, next_dex = parse(system_string, next_dex, '<end>')
	end, next_dex = parse(system_string, next_dex, '<capture>')
	capture, next_dex = parse(system_string, next_dex, '<targets>')
	targets, next_dex = parse(system_string, next_dex, '||')


	#parse variables and their values
	# variables are always constant
	sub_var_string = variables[variables.find('>') + 1:].split(',')
	if sub_var_string[0]:
		variables, var_vals = zip(*[vari.split(':') 
					for vari in sub_var_string])
		var_vals = [float(amt) for amt in var_vals]

	else: variables, var_vals = [], []


	#initialize the current state vector, counts
	#counts should follow the form:
	# ['null', 'iteration', 'time', 'fixed_time', species1, ..., speciesN, variable1, ..., variableM, function1, ..., functionR]
	#count_targets is a 1 - 1 list of labels for these data slots
	species, counts = zip(*[spec.split(':') for spec in 
			species[species.find('>') + 1:].split(',')])
	count_targets = ['null', 'iteration', 'time', 'fixed_time'] + \
									list(species) + list(variables)
	counts = [0, iteration, time, fixed_time] + \
			[int(amt) for amt in counts] + var_vals


	#functions depend on variables and species - initialize and add last
	#parse functions and calculate their initial values
	#functions may not depend on each other
	functions = functions[functions.find('>') + 1:].split(',')
	if functions[0]:
		func_names, functions = generate_functions(
				functions, count_targets, counts)

	else: func_names, functions = [], []
	count_targets.extend(func_names)
	counts.extend([func(counts) for func in functions])
	update_functions = generate_update_functions(
		count_targets, counts, functions, func_names)
	#functions are captured but not updated in the counts lists


	#parse and create the reactions
	rxn_split = rxns[rxns.find('>') + 1:].split(',')
	rate_call_group = []
	propensities, validators, reactions, reagents, products =\
			zip(*[generate_reaction(count_targets, counts, functions, 
							func_names, var_vals, variables, 
								rxn_string, rate_call_group) 
								for rxn_string in rxn_split])

	#maintain propensities in one to one with reactions
	#only update when necessary; initialize here
	propensity_count = len(rxn_split)
	cdef double [:] propensity_table
	propensity_table = np.zeros(propensity_count)
	for dex, prop in enumerate(propensities):
		propensity_table[dex] = prop()

	#wrap propensities so that each instead function
	# instead updates the propensity which its corresponding rxn
	#  modified while reacting
	#subsequently call rxn's propensity function post-reacting
	propensities = wrap_propensities(propensity_table, 
		propensities, reagents, products, rate_call_group)
	#could/should the same thing be done with functions?
	# could update a function_values table before capture
	# also update function_values table based on reactions
	#  effect on the system (changes in species count, time, etc)
	# thus a function would only not need to be updated if it
	#  depends on no species whose count changed not on time/fixed_time


	#targets string parsed into a list or strings
	# targets can be species, variables, or functions
	#initialize output data structure
	targets = targets[targets.find('>') + 1:].split(',')
	targets = follow_order(targets, count_targets)

	#DETERMINE TOTAL POINTS, REWRITE ALGORITHM SO EXACTLY THIS MANY CAPTURES OCCUR
	# KEEP THE DATA IN A NP MATRIX!!!
	data = [[] for dex in range(len(count_targets))]
	target_dexes = [count_targets.index(targ) for targ in targets]


	#create a function which tests if the simulation should end
	ends = end[end.find('>') + 1:].split(',')
	end_test = generate_test(count_targets, data, counts, ends)


	#create a function which tests of the current state 
	# of the system should be captured
	#create a function which captures the current state of the system
	capts = capture[capture.find('>') + 1:].split(',')
	capture_test = generate_test(count_targets, data, counts, capts)
	capture = generate_capture_function(data, target_dexes, counts)


	#if 'time' is used for capture criteria, 
	# inherit increment for fixed_delt
	uses_time = ['time' in spl for spl in capts]
	if True in uses_time:
		capt = capts[uses_time.index(True)]
		fixed_delt = float(capt[capt.rfind(':') + 1:])


	#use the genrand class to generate all random numbers at once
	cdef int seed = int(random.random()*10000000.0)
	cdef GENRAND rndvar = GENRAND(seed = seed)


	#initilize the rxn_table
	cdef double [:] rxn_table
	rxn_table = np.zeros(propensity_count)


	#capture the initial state of the system
	capture()

	#the simulation loop
	while not end_test():
		#calculate the rxn_table - for rxn selection
		propensity_total = 0.0 #sum(propensity_table)
		for prop_dex in range(propensity_count):
			if validators[prop_dex]():
				propensity_total += propensity_table[prop_dex]

			rxn_table[prop_dex] = propensity_total

		#if at least one rxn propensity is greater than zero, 
		# normalize the rxn_table
		if propensity_total > 0.0:
			propensity_total_inv = 1.0/propensity_total
			for dex in range(propensity_count):
				rxn_table[dex] = rxn_table[dex] * propensity_total_inv

		#else all reactions are impossible; end the simulation
		else:
			timedex = len(data) - 1
			bad_dex = validate_data(data, timedex)
			print 'all reactions impossible; ending'
			return data, targets, bad_dex

		#choose a reaction based on the updated rxn_table
		#rand_rxn = random.random()
		rand_rxn = rndvar.gen()
		rxn_dex = pick_reaction(rxn_table, rand_rxn, propensity_count)

		#update the iteration, time
		iteration += 1
		counts[1] = iteration
		rand_time = rndvar.gen()
		#rand_time = random.random()
		time_step = -1.0 * log(rand_time) * propensity_total_inv
		time = (last_time + time_step)
		last_time = time
		counts[2] = time

		#if the capture criteria are met, 
		# perform capture and update fixed_time
		if capture_test():
			fixed_time_step = time - data[3][-1]
			fixed_steps = int((fixed_time_step + fixed_delt) / fixed_delt)
			step = 0
			while step < fixed_steps:
				fixed_time = last_fixed_time + fixed_delt
				last_fixed_time = fixed_time
				counts[3] = fixed_time
				update_functions()
				capture()
				step += 1
			'''
			for fixed_update in range(fixed_steps):
				fixed_time = last_fixed_time + fixed_delt
				last_fixed_time = fixed_time
				counts[3] = fixed_time
				update_functions()
				capture()
			'''

		#react the chosen reaction which modifies the counts vector
		#update the propensities which depended on this rxn's
		# change to the system state
		reactions[rxn_dex]()
		propensities[rxn_dex]()

	#hack fix to capture of last time point
	remainder_time = time - fixed_time
	if (remainder_time > fixed_delt):
		fixed_time = last_fixed_time + fixed_delt
		last_fixed_time = fixed_time
		counts[3] = fixed_time
		update_functions()
		capture()

	#list of labels in 1 - 1 correspondance with data lists
	return data, targets



#__main__ entry point used for profiling using the default system string
if __name__ == '__main__': simulate()


