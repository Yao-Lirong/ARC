from interpreter_log import *
import time
from itertools import chain, combinations
from functools import reduce

DEBUG = False
BACKGROUND_COLOR = Color.Black

def read_task(taskname, index, inpt = True):
	"""
	Return the input/output of `index`th example of `taskname`
	Returns input if `inpt` is True, returns output if it's False
	"""
	filename = taskname + ".json"
	with open(os.path.join(os.getcwd(), "ARCdata\\data\\training\\") + filename) as f:
		j = json.load(f)
	datas = j["train"]
	data = datas[index]
	return data["input"] if inpt else data["output"]


TASKNAME, TASKNUM, ISINPUT = "025d127b", 0, True
alpha = 1

canvas = np.array(read_task(TASKNAME, TASKNUM, ISINPUT))
canvas = np.array([[0, 1, 1], [1, 2, 0]])


target = array_to_canvas(canvas)
display(target)

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
canvas_colors_num = len(target_colors)


start_time = time.time()

color_count = [ [ [ [np.zeros(10) for _ in range(ylen-y)] for _ in range(xlen-x)] for y in range(ylen)] for x in range(xlen)]
# 加一个这里有没有colored pixel可以优化速度


for x in range(xlen):
	for y in range(ylen):
		c = target[x][y]
		color_count[x][y][0][0][c] += 1
for xl in range(1, xlen):
	color_count[0][0][xl][0] = color_count[0][0][xl-1][0] + color_count[0+xl][0][0][0]
for yl in range(1, ylen):
	color_count[0][0][0][yl] = color_count[0][0][0][yl-1] + color_count[0][0+yl][0][0]

if DEBUG: print([(x, y, color_count[x][y][0][0]) for x in range(xlen) for y in range(ylen)])

for xl in range(1, xlen):
	for yl in range(1, ylen):
		color_count[0][0][xl][yl] = color_count[0][0][xl-1][yl] + color_count[0][0][xl][yl-1] \
							- color_count[0][0][xl-1][yl-1] + color_count[0+xl][0+yl][0][0]
		if DEBUG: print((0, 0, xl, yl) , color_count[0][0][xl][yl])

a = 1

for x in range(1, xlen):
	for xl in range(xlen-x):
		for yl in range(ylen):
			if xl + yl == 0: continue
			color_count[x][0][xl][yl] = color_count[0][0][x+xl][yl] - color_count[0][0][x-1][yl]
			if DEBUG: print((x, 0, xl, yl) , color_count[x][0][xl][yl])

for y in range(1, ylen):
	for xl in range(xlen):
		for yl in range(ylen-y):
			if xl + yl == 0: continue
			color_count[0][y][xl][yl] = color_count[0][0][xl][y+yl] - color_count[0][0][xl][y-1]
			if DEBUG: print((0, y, xl, yl) , color_count[0][y][xl][yl])

a = 2

for x in range(1, xlen):
	for y in range(1, ylen): 
		for xl in range(xlen - x):
			for yl in range(ylen - y):
				color_count[x][y][xl][yl] = color_count[0][0][x+xl][y+yl] + color_count[0][0][x-1][y-1] \
									 - color_count[0][0][x-1][y+yl] - color_count[0][0][x+xl][y-1]
				if DEBUG: print((x, y, x+xl, y+yl) , color_count[x][y][xl][yl])


a = 3


# Convert to Usable Preprocessed Values

def powerset_without_empty_or_singleton(iterable):
    """
	@Requires len(iterable) > 1
	@Example powerset([1,2,3]) --> (1,2) (1,3) (2,3) (1,2,3)
	"""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(2, len(s)+1))

def bitmap_color_comb_with_bgcolor(c):
	return list(filter(lambda lst : BACKGROUND_COLOR in lst,
			           powerset_without_empty_or_singleton(c)))

"""
好聪明的一个优化
"""
canvas_by_color = {}
for c in target_colors:
	canvas_by_color[c] = np.where(target == np.array(c), True, False)

canvas_by_color_comb = {}
mask_by_color_comb = {}
for cc in bitmap_color_comb_with_bgcolor(target_colors):
	cc = tuple(sorted(cc))
	this_bitmap_mask = np.array(reduce(lambda acc, tc : canvas_by_color[tc] + acc, cc, np.array(np.zeros((xlen, ylen)), dtype = bool)))
	this_bitmap = np.where(this_bitmap_mask, target, Color.Black)
	mask_by_color_comb[cc] = this_bitmap_mask
	canvas_by_color_comb[cc] = this_bitmap

bitmaps = []
bitmap_commands = []
bitmap_masks = []
bitmap_costs = []

for x in range(xlen):
	for y in range(ylen):
		for xl in range(xlen - x):
			for yl in range(ylen - y):
				
				color_count_with_bg = color_count[x][y][xl][yl]
				color_count_with_bg[BACKGROUND_COLOR] += 1
				cc = tuple(np.where(color_count_with_bg != 0)[0])
				color_comb = bitmap_color_comb_with_bgcolor(cc)
				
				print("-----------")
				print((x, y, x+xl, y+yl) , cc)
				
				for c in color_comb:

					assert BACKGROUND_COLOR in c

					this_bitmap_mask = np.full((xlen, ylen), False)
					this_command = obj("cheat", x, y, c, xlen = xl+1, ylen = yl+1)
					
					this_bitmap_mask[x:x+xl+1, y:y+yl+1] = mask_by_color_comb[c][x:x+xl+1, y:y+yl+1]
					
					if np.sum(np.sum(this_bitmap_mask)) == 0: 
						print("!!!")
						print(c)
						print((x, y, x+xl, y+yl) , color_count[x][y][xl][yl])
						raise Exception("WHAT?")
					
					""" Duplicate Code with Bitmap Cost Preprocessing, 
						need to Change Both sections when making changes
						This section is kept for better performance. """
					# TODO 根据怎么选颜色改，现在是任何 bitmap 都从 target_colors 里面选
					this_color_count = color_count[x][y][xl][yl][(c,)]
					this_command_cost = dirichlet_multinom_cost(np.pad(this_color_count, (0, len(target_colors) - len(this_color_count)), "constant"))
					# this_command_cost = dirichlet_multinom_cost([colored_bits, xl*yl - colored_bits], self.alpha) + baseline_cost + theta_bm_cost
					
					print(this_command, this_command_cost)
					display(this_bitmap_mask)

					bitmaps.append(canvas_by_color_comb[c])
					bitmap_masks.append(this_bitmap_mask)
					bitmap_commands.append(this_command)
					bitmap_costs.append(this_command_cost)


end_time = time.time()
print(end_time - start_time)