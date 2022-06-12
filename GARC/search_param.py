from statistics import mean
from interpreter_log import *
import argparse

parser = argparse.ArgumentParser()
# data I/O
parser.add_argument('-a', '--alpha', type = float, default = 1.0, 
					help='alpha value in Dirichlet Distribution')
parser.add_argument('-th','--theta', nargs='+', type = float,
					default = [1.0, 1.0, 1.0, 1.0],
					help='four theta value of dot, line, rectangle, and bitmap')
parser.add_argument('-r', '--random-search', action = "store_true",
					# type = bool, default = False,
					help='If set to True, ignores all hyperparameter arguments and draw them at random')

args = parser.parse_args()

def draw_random_alpha_theta():
	alpha_range = list(range(-10, 5, 0.1))
	log_theta_range = list(range(20, step=0.1))
	args.alpha = np.exp(random.choice(alpha_range))
	log_thetas = [random.choice(log_theta_range) for _ in range(3)]
	log_thetas.append(random.choice(range(6, step=0.1)))
	args.theta = list(map(lambda t : t - logsumexp(log_thetas), log_thetas))
	args.theta = list(np.multiply(-1, args.theta))

if args.random_search: 
	# When we randomly draw, we draw the value of alpha and the value of theta
	alpha_range = list(range(-10, 10))
	log_theta_range = list(range(20))
	args.alpha = np.exp(random.choice(alpha_range))
	log_thetas = [random.choice(log_theta_range) for _ in range(4)]
	args.theta = list(map(lambda t : t - logsumexp(log_thetas), log_thetas))
else:
	# When a user specifies, he gives value of theta and the cost of each command
	# Here for theta, we convert them to the -logP form first then normalize
	args.theta = list(np.multiply(-1, args.theta))
	args.theta = list(map(lambda t : t - logsumexp(args.theta), args.theta))

print("Alpha: ", args.alpha)
print("Theta Probabilities: ", end="")
print(["{0:0.2f}".format(t) for t in np.exp(args.theta) * 100])
# we now have the log probability, but -log probability is the cost
args.theta = list(np.multiply(-1, args.theta))
print("Theta Costs: ", end="")
print(["{0:0.2f}".format(t) for t in args.theta])
print("\n\n\n\n\n")



astar = Astar(args.alpha, args.theta)

tasks = [

	# 下半部分向左移动
	("025d127b", 0, True), 
	("025d127b", 1, True), 

	# bitmap:移动红色物体到蓝色方块旁边
	("05f2a901", 0, True), 
	("05f2a901", 1, True), 
	("05f2a901", 2, True), 

	# 根据高度上色
	("08ed6ac7", 0, True),

	# 根据点的位置画竖线，输入就是两个点
	("0a938d79", 0, True), 
	("0a938d79", 1, True), 

	# 分割方块
	("1190e5a7", 0, True), 
	("1190e5a7", 1, True), 

	# 根据中心灰色方块拼接物体
	("137eaa0f", 0, True), 

	# 给阴影上色，横线蓝，方块红
	("150deff5", 0, False), 
	("150deff5", 1, False), 
	("150deff5", 2, False), 

	# 根据蓝绿红画横竖线
	("178fcbfb", 0, True), 
	("178fcbfb", 1, True), 
	("178fcbfb", 2, True), 
	("178fcbfb", 0, False), 
	("178fcbfb", 1, False), 
	("178fcbfb", 2, False), 

	# 移动颜色相同的点，删除颜色不同的点
	("1a07d186", 0, True), 
	("1a07d186", 1, True), 
	("1a07d186", 2, True), 
	("1a07d186", 0, False), 
	("1a07d186", 1, False), 
	("1a07d186", 2, False), 

	

	# ("05269061", True)
]

task_costs = []
solution_ranks = []
for task in tasks:
	(taskname, tasknum, isinput) = task

	print("vvvvvvvv %s %d vvvvvvvv" %(taskname, tasknum))
	sol_rank, diff = astar.search_one(taskname, tasknum, isinput)
	astar.reset()
	print("\n\n")
	task_costs.append(diff)
	solution_ranks.append(sol_rank)
print("\n\n\n\n\n")

for task in zip(tasks, solution_ranks ,task_costs): print(task)

# rank and cost of those that are actually found (with a rank > 0)
rank_cost = list(filter(lambda rc : rc[0]>0, zip(solution_ranks ,task_costs))) 

print(mean(task_costs), min(task_costs), max(task_costs))

"""
If no solution is found (rank_cost is an empty list), 
mean will throw an error, causing nothing to be print out.
So when we run the summary, no summary will be generated for this set of parameters,
which meets our expectation because it didn't find anything.
"""

# the average of loss (excluding 0s)
print(mean(list(map(lambda rc : rc[1], rank_cost))))
# the number of solutions actually found in the first 1000 predictions
print(len(rank_cost))