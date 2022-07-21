from functools import reduce
import json
import queue
import time
import cProfile
import tracemalloc
import os
from API.canvas import *
from API.color import *
from obj_a_log import *
from scipy.special import loggamma, logsumexp

RUNTIME = 600.0
WANTED_RESULTS_NUM = 5000
TOPRINT_RESULTS_NUM = 10
assert TOPRINT_RESULTS_NUM <= WANTED_RESULTS_NUM
PRINT_FREQUENCY = 10000000
SERVER = True
ENABLE_PROFILER = False
ENABLE_LEGACY = False
# parent_dir = os.path.dirname(os.getcwd())
arc_dir = "/home/ly373/ARC/" if SERVER \
			   else os.path.join(os.getcwd(), "ARCdata\\data\\training\\")
# RUNTIME = 5.0

def array_to_canvas(arr):
	"""
	Convert np array `arr` into our API coordinate system
	"""
	return np.rot90(arr, 3)

def canvas_to_array(cnv):
	"""
	Convert `cnv` of our API coordinate system into the np array coordinate system
	"""
	return np.rot90(cnv)

def read_task(taskname, index, inpt = True):
	"""
	Return the input/output of `index`th example of `taskname`
	Returns input if `inpt` is True, returns output if it's False
	"""
	filename = taskname + ".json"
	with open(arc_dir + "ARCdata/data/training/" + filename) as f:
		j = json.load(f)
	datas = j["train"]
	data = datas[index]
	return data["input"] if inpt else data["output"]


tp_dots = ["dot"]
tp_lines = ["vertical", "parallel", "diagonal_ur", "diagonal_ul"]
tp_recs = ["rectangle", "outline"]
types = tp_dots + tp_lines + tp_recs

# functions to create the objects
def dot(xlen, ylen, x, y, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	mask_canvas = np.array(obj_canvas, dtype = bool)
	obj_canvas[x, y] = c
	mask_canvas[x, y] = True
	return obj_canvas, mask_canvas

def rectangle(xlen, ylen, x, y, xl, yl, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	obj = np.full((xl,yl), c, dtype=int)
	obj_canvas[x:x+xl, y:y+yl] = obj
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def outline(xlen, ylen, x, y, xl, yl, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	obj_canvas[x:x+xl, y] = obj_canvas[x:x+xl, y+yl] = obj_canvas[x, y:y+yl] = obj_canvas[x+xl, y:y+yl] = c
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def vertical_line(xlen, ylen, x, y, l, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	obj = np.full((1,l), c, dtype = int)
	obj_canvas[x:x+1, y:y+l] = obj
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def parallel_line(xlen, ylen, x, y, l, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	obj = np.full((l,1), c, dtype = int)
	obj_canvas[x:x+l, y:y+1] = obj
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def diagonal_line_upright(xlen, ylen, x, y, l, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	for i in range(l):
		obj_canvas[x+i][y+i] = c
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def diagonal_line_upperleft(xlen, ylen, x, y, l, c):
	obj_canvas = np.zeros((xlen, ylen), dtype = int)
	for i in range(l):
		obj_canvas[x-i][y+i] = c
	mask_canvas = np.array(obj_canvas, dtype = bool)
	return obj_canvas, mask_canvas

def hash_canvas(canvas):
	return hash(tuple(map(tuple, canvas)))

def dirichlet_multinom_cost(counts, alpha = 1):
	n = sum(counts)
	K = len(counts)
	res = loggamma(K * alpha) + loggamma(n+1) - loggamma(n + K*alpha)
	for k in range(K):
		res += loggamma(counts[k]+alpha) - loggamma(alpha) - loggamma(counts[k]+1)
	return -res



class Astar():

	def __init__(self, alpha, theta):
		self.alpha = alpha
		self.theta = theta
		
		"""
		node: hash_canvas -> [canvas, preds]
		where `canvas` is the np representation of the state/canvas we are in 
		`preds` is a list of hash of the predecessors of this canvas
		"""
		self.nodes = {}
		"""
		self.edges: (hash_u, hash_v) -> commands
		`hash_u` and `hash_v` are hash of two canvases
		`commands` contains a list of commands that can transform canvas u into v
		"""
		self.edges = {}

		self.total_iterations = 0
		self.solution_program = None

	def reset(self):
		self.nodes = {}
		self.edges = {}
		self.total_iterations = 0
		self.solution_program = None

	def solution_by_type(self, j):
		sol = {}
		sol["dot"] = list(filter(lambda o : o["type"] in tp_dots, j))
		sol["line"] = list(filter(lambda o : o["type"] in tp_lines, j))
		sol["rec"] = list(filter(lambda o : o["type"] in tp_recs, j))
		sol["bitmap"] = list(filter(lambda o : o["type"] == "cheat", j))
		return sol

	def search_aux(self, target):
		# q may store states with the same canvas but of different cost
		# vis only records whether a state with that canvas is visited or not, 
		# regardless of the cost that is to say, after visiting a canvas once, 
		# we don't want to visit the same canvas but with a higher cost
		# Why not just use update_priority? Python doesn't support this.
		target = np.array(target)
		q = queue.PriorityQueue()
		vis = set()
		xlen = x_length(target)
		ylen = y_length(target)
		maxlen = max(xlen, ylen)
		area = xlen * ylen

		target_colors = list(filter(
			lambda c : np.sum(np.sum(np.where(target == np.array(c), True, False))) != 0, 
			non_black_colors))
		target_colors += [Color.Black] # always include black
		target_colors_num = len(target_colors)

		def norm_factor():
			# line_bitmap = dirchilet_multinom_cost([max(xlen, ylen), 0], self.alpha) + np.log(target_colors_num)
			# rec_bitmap = dirchilet_multinom_cost([area, 0], self.alpha) + np.log(target_colors_num)
			# dot_bitmap = dirchilet_multinom_cost([1, 0], self.alpha) + np.log(target_colors_num)
			# print("Calculating Bitmap Factor")
			# print("normal line " +  str(line_cost) + " | line as bitmap " + str(line_bitmap))
			# print("normal rec " +  str(rec_cost) + " | rec as bitmap " + str(rec_bitmap))
			# print("normal dot " +  str(dot_cost) + " |  dot as bitmap " + str(dot_bitmap))
			# factor = max(line_cost / line_bitmap, rec_cost / rec_bitmap, dot_cost / dot_bitmap)
			# print("Bitmap Factor is " + str(factor) +"\n")

			"不对，应该取最小的 rec line dot 而不是最大的面积，最小的面积才能有最小的dirichlet score，才能算出最大的 factor"
			dot_bitmap = dirichlet_multinom_cost([1, 0], self.alpha) + np.log(target_colors_num)
			factor = rec_cost / dot_bitmap
			print("Bitmap Factor is " + str(factor) +"\n")
			return factor

		theta_dot_cost, theta_line_cost, theta_rec_cost, theta_bm_cost = self.theta 
		dot_cost = np.log(area) + np.log(target_colors_num) + theta_dot_cost
		line_cost = np.log(area * max(xlen, ylen) * target_colors_num) + theta_line_cost
		rec_cost = 2 * np.log(area) + np.log(target_colors_num) + theta_rec_cost
		baseline_cost = 2 * np.log(area) + np.log(target_colors_num)
		bitmap_factor = 1 # * norm_factor()
		# new_object_cost = 1 # user-defined new object cost
		# cheating_cost = area # user-defined all cover cost

		""" 
		TODO
		Duplicate Code with Bitmap Cost Preprocessing
		Need to Change Both sections when making changes
		"""
		def bitmap_cost(bitmap):
			bitmap = np.array(bitmap, dtype = bool)
			xl = len(bitmap)
			yl = len(bitmap[0])
			colored_bits = np.sum(np.sum(bitmap))
			cbitmap = dirichlet_multinom_cost([colored_bits, xl*yl - colored_bits], self.alpha) \
					+ baseline_cost + theta_bm_cost
			return cbitmap

		def get_desired_cost(prog):
			res = 0
			res += len(prog["dot"]) * dot_cost
			res += len(prog["line"]) * line_cost
			res += len(prog["rec"]) * rec_cost
			res = reduce(lambda x,y : x + bitmap_cost(y["bitmap"]), prog["bitmap"], res)
			return res
		
		desired_cost = get_desired_cost(self.solution_program)
		final_states = []
		
		def diff_to_target(canvas): return np.sum(np.sum(canvas != target))
		def heuristic_distance(canvas):
			diff_num = diff_to_target(canvas)
			if diff_num == 0: return 0
			diff_canvas = target[canvas != target]
			diff_color_kind = len(set(diff_canvas.flatten()))
			# return np.log(area * diff_color_kind * diff_num) # now
			return diff_num * np.log(area * diff_color_kind) # kevin

		blank_canvas = new_canvas(xlen, ylen)
		start_state = state(blank_canvas)
		if ENABLE_LEGACY: self.nodes[hash(start_state)] = [start_state.canvas, []]
		q.put(start_state)

		# Preprocess possible objects to draw
		objs = [] # a list of all possible objects to be drawn
		obj_commands = [] # a list of the corresponding commands to generate those objects
		obj_masks = []

		for tp in types:
			if tp in tp_dots:
				for x in range(xlen):
					for y in range(ylen):
						for c in target_colors:
							this_command = obj(tp, x, y, c)
							this_obj, this_mask = dot(xlen, ylen, x, y, c)
							obj_masks.append(this_mask)
							objs.append(this_obj)
							obj_commands.append(this_command)
			if tp in tp_lines:
				for l in range(1, maxlen+1):
					for x in range(xlen):
						for y in range(ylen):
							for c in target_colors:
								this_command = obj(tp, x, y, c, l = l)
								if tp == "vertical":
									if l > ylen - y: continue
									this_obj, this_mask = vertical_line(xlen, ylen, x, y, l, c)
								elif tp == "parallel":
									if l > xlen - x: continue
									this_obj, this_mask = parallel_line(xlen, ylen, x, y, l, c)
								elif tp == "diagonal_ur":
									if l > xlen - x or l > ylen - y: continue
									this_obj, this_mask = diagonal_line_upright(xlen, ylen, x, y, l, c)
								elif tp == "diagonal_ul":
									if l > xlen - x or l > ylen - y: continue
									this_obj, this_mask = diagonal_line_upperleft(xlen, ylen, x, y, l, c)
								obj_masks.append(this_mask)
								objs.append(this_obj)
								obj_commands.append(this_command)
			elif tp in tp_recs:
				for x in range(xlen):
					for y in range(ylen):
						for xl in range(1, xlen - x + 1):
							for yl in range(1, ylen - y + 1):
								for c in target_colors:
									# rectangle will always be inside the boundary since for loop checks for it
									this_command = obj(tp, x, y, c, xlen = xl, ylen = yl)
									this_obj, this_mask = rectangle(xlen, ylen, x, y, xl, yl, c)
									obj_masks.append(this_mask)
									objs.append(this_obj)
									obj_commands.append(this_command)



		""" Preprocess possible bitmaps to draw	"""
		bitmaps = []
		bitmap_commands = []
		bitmap_masks = []
		bitmap_costs = []

		for c in target_colors:

			bitmap_mask = np.where(target == np.array(c), True, False)
			bitmap = np.where(target == np.array(c), c, Color.Black)
			
			for x in range(xlen):
				for y in range(ylen):
					for xl in range(1, xlen - x + 1):
						for yl in range(1, ylen - y + 1):
							this_bitmap_mask = np.full((xlen, ylen), False)
							this_command = obj("cheat", x, y, c, xlen = xl, ylen = yl)
							
							this_bitmap_mask[x:x+xl, y:y+yl] = bitmap_mask[x:x+xl, y:y+yl]
							if np.sum(np.sum(this_bitmap_mask)) == 0: continue # if there is nothing to draw for this color in this region, we just skip this region
							colored_bits = np.sum(np.sum(this_bitmap_mask))
							
							""" Duplicate Code with Bitmap Cost Preprocessing, 
								need to Change Both sections when making changes
								This section is kept for better performance. """
							this_command_cost = dirichlet_multinom_cost([colored_bits, xl*yl - colored_bits], self.alpha) + baseline_cost + theta_bm_cost
							# this_command_cost = bitmap_factor * this_command_cost
							
							bitmaps.append(bitmap)
							bitmap_masks.append(this_bitmap_mask)
							bitmap_commands.append(this_command)
							bitmap_costs.append(this_command_cost)


		""" Start to Search """
		start_time = time.time()
		counter = 0 
		# previous_state = None
		# global this_state
		# this_state = None

		while not q.empty():#  and time.time() - start_time < RUNTIME:
			
			# if time.time() - start_time > RUNTIME:
			# 	print("OUT OF TIME, TERMINATE")
			# 	return
			# previous_state = this_state
			this_state = q.get()
			this_hash = hash(this_state)

			self.total_iterations += 1
			counter += 1
			if counter == PRINT_FREQUENCY:
				print("iterating new state with cost %f, heuristic distance %f" %(this_state.command_cost, this_state.cost - this_state.command_cost))
				display(this_state.canvas)
				self.print_path_state(this_state, True)
				counter = 0
					
			if this_hash in vis:
				# print("Yes Used, WHAT??")
				# self.print_path_state(this_state)
				# print("\n\n")
				continue
			vis.add(this_hash)
			this_canvas = this_state.canvas
			this_command_cost = this_state.command_cost

			# Search Regular Objects
			next_canvases = np.where(obj_masks, objs, this_canvas)
			for i in range(len(next_canvases)):
				next_canvas = next_canvases[i]

				if diff_to_target(next_canvas) >= diff_to_target(this_canvas): continue

				next_command = obj_commands[i]
				next_hash = hash_canvas(next_canvas)
				if ENABLE_LEGACY:
					if next_hash not in self.nodes: 
						self.nodes[next_hash] = [next_canvas, [this_canvas]]
					else:
						self.nodes[next_hash][1].append(this_canvas)

				hrstc_dis = heuristic_distance(next_canvas)
				next_command_cost = this_command_cost + \
									(rec_cost if next_command.type == "rectangle" else \
									dot_cost if next_command.type == "dot" else line_cost)
				next_cost = next_command_cost + hrstc_dis
				next_state = state(next_canvas, next_cost, next_command_cost, this_state, next_command, next_hash)
				
				if ENABLE_LEGACY:
					if (this_hash, next_hash) not in self.edges:
						self.edges[(this_hash, next_hash)] = [(next_command, next_cost, hrstc_dis)]
					else:
						self.edges[(this_hash, next_hash)].append((next_command, next_cost, hrstc_dis))

				if hrstc_dis == 0: 
					final_states.append(next_state)
					if next_cost == desired_cost: print("Found Desired Program at iteration %d" %(self.total_iterations))
					if len(final_states) == WANTED_RESULTS_NUM: return final_states, desired_cost
				# put in queue only if it is not a final state and it was not visited
				elif next_hash not in vis: q.put(next_state)

			# Search Cheating yet Expensive Shortcuts
			next_canvases = np.where(bitmap_masks, bitmaps, this_canvas)
			for i in range(len(next_canvases)):
				next_canvas = next_canvases[i]

				# TODO: only considers the commands that improve the cost
				if diff_to_target(next_canvas) >= diff_to_target(this_canvas): continue

				next_command = bitmap_commands[i]
				next_hash = hash_canvas(next_canvas)
				if ENABLE_LEGACY:
					if next_hash not in self.nodes: 
						self.nodes[next_hash] = [next_canvas, [this_canvas]]
					else:
						self.nodes[next_hash][1].append(this_canvas)
				
				hrstc_dis = heuristic_distance(next_canvas)
				next_command_cost = this_command_cost + bitmap_costs[i]
				next_cost = next_command_cost + hrstc_dis
				next_state = state(next_canvas, next_cost, next_command_cost, this_state, next_command, next_hash)
				
				if ENABLE_LEGACY:
					if (this_hash, next_hash) not in self.edges:
						self.edges[(this_hash, next_hash)] = [(next_command, next_cost, hrstc_dis)]
					else:
						self.edges[(this_hash, next_hash)].append((next_command, next_cost, hrstc_dis))

				if hrstc_dis == 0: 
					final_states.append(next_state)
					if next_cost == desired_cost: print("Found Desired Program at iteration %d" %(self.total_iterations))
					if len(final_states) == WANTED_RESULTS_NUM: return final_states, desired_cost

				elif next_hash not in vis: q.put(next_state)

		return final_states, desired_cost

	def print_path_state(self, final_state, edge_only=False):
		xlen = x_length(final_state.canvas)
		ylen = y_length(final_state.canvas)
		blank_canvas = new_canvas(xlen, ylen)
		current = final_state
		path = []
		while hash(current) != hash_canvas(blank_canvas):
			if not edge_only: display(current.canvas)
			print(current.edge, current.command_cost)
			current = current.parent
		if not edge_only: display(blank_canvas)
		return path
		
	def sorted_states_by_command_cost(self, states):
		for state in states: assert(state.command_cost == state.cost)
		return sorted(states, key = lambda x : x.cost)

	def search_one(self, taskname, tasknum, isinput):
		
		canvas = np.array(read_task(taskname, tasknum, isinput))
		with open(arc_dir + "GARC/annotation/" + taskname + ("_i" if isinput else "_o") + ".json") as f:
			sol_json = json.load(f)
		# sol = __import__("p_" + taskname + ("_i" if isinput else "_o"))

		self.solution_program = self.solution_by_type(sol_json[tasknum])


		canvas = array_to_canvas(canvas)
		display(canvas)

		if ENABLE_PROFILER:
			profiler = cProfile.Profile()
			profiler.enable()
			tracemalloc.start()

		predictions, solution_cost = self.search_aux(canvas)

		if ENABLE_PROFILER:
			profiler.disable()
			profiler.dump_stats("/home/ly373/ARC/GARC/search.stats")

			print("maximum memory usage is " + str(tracemalloc.get_traced_memory()[1] / 1024 / 1024 / 1024) + " Gb")
			tracemalloc.stop()
		
		print("Looking for a program with cost " + str(solution_cost))
		print("Used a total %d iterations" %(self.total_iterations))

		# for i in range(len(res)):
		# 	print("---------%d---------" %(i))
		# 	self.print_path_state(res[i])
		# 	print("---------%d---------" %(i))

		# print ("!!!!!!!!!! SORTED !!!!!!!!!!")
		sorted_prediction = self.sorted_states_by_command_cost(predictions)
		solution_rank = -1
		for i in range(len(sorted_prediction)):
			if sorted_prediction[i].command_cost == solution_cost:
				solution_rank = i+1
		print("solution ranked at " + str(solution_rank) \
			if solution_rank > 0 else "solution not found")
		for i in range(TOPRINT_RESULTS_NUM):
			print("---------%d---------" %(i))
			self.print_path_state(sorted_prediction[i], True)
			print("---------%d---------" %(i))
		
		return (solution_rank, 
				solution_cost - sorted_prediction[0].command_cost)





if __name__ == "__main__":

	# test for parallel and vertical line
	# canvas = np.array(([5,5,5], [0,0,3], [0,0,3]))
	# test for diagonal line
	# canvas = np.array([[0,0,1],[0,1,0],[1,0,0]])
	# test for square
	# canvas = np.array([[0,1,1],[0,1,1],[1,0,0]])

	# 切方块
	TASKNAME, TASKNUM, ISINPUT = "1190e5a7", 0, True

	# 切方块
	# canvas = np.array(read_task("1190e5a7", 0, True))
	# 画斜线
	# canvas = np.array(read_task("05269061", 1, False))
	# Rand Object
	# canvas = np.array(read_task("0520fde7", 2, True))

	# canvas = np.array(read_task("06df4c85", 2, True))

	# search_one(TASKNAME, TASKNUM, ISINPUT)

	TASKNAME, TASKNUM, ISINPUT = "0a938d79", 0, True

	TASKNAME, TASKNUM, ISINPUT = "025d127b", 0, True
	
	alpha, theta = 0.0009118819655545162, [14.0, 15.0, 15.0, 11.0]
	theta = list(np.multiply(-1, theta))
	theta = list(map(lambda t : t - logsumexp(theta), theta))
	print("Alpha: ", alpha)
	print("Theta Probabilities: ", end="")
	print(["{0:0.2f}".format(t) for t in np.exp(theta) * 100])
	# we now have the log probability, but -log probability is the cost
	theta = list(np.multiply(-1, theta))
	print("Theta Costs: ", end="")
	print(["{0:0.2f}".format(t) for t in theta])
	print("\n\n\n\n\n")
	astar = Astar(alpha, theta)
	astar.search_one(TASKNAME, TASKNUM, ISINPUT)