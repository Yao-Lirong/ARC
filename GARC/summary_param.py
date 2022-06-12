import os, re
import matplotlib.pyplot as plt

DIR = "/home/ly373/ARC/GARC/"
filenames = os.listdir(DIR)
zult_names = list(filter(lambda s : re.match("zult_\d+\.out", s), filenames))
print("These tasks are not included in the summary:")

task_costs  = []
sols_found = []
valid_zult_names = []
for zult_name in zult_names:
	f = open(DIR + zult_name, 'r', encoding='utf-8')
	lines = f.readlines()
	# print(zult_name, lines[-2])
	try:
		task_cost = float(lines[-2])
		sol_found = int(lines[-1])
	except:
		print(zult_name)
		continue

	valid_zult_names.append(zult_name)
	task_costs.append(task_cost)
	sols_found.append(sol_found)

fig, plot = plt.subplots()
plot.scatter(sols_found, task_costs)
zults = list(map(lambda s : re.search("\d+", s).group(0), valid_zult_names))
for i, txt in enumerate(zults):
    plot.annotate(txt, (sols_found[i], task_costs[i]))

plot.xaxis.get_major_locator().set_params(integer=True)

plt.savefig('zz.png')

print("\n\n", task_costs, sols_found)
print(zults)