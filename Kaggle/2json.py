import json
import os
dir_path = os.getcwd() + "/output/"

def to_canvas(res):
	result = res.split("|")
	score = result[-1]
	canvas = result[1:-1]
	canvas = list(map(lambda row : [int(x) for x in row], canvas))
	return canvas

answer_range = range(0, 40)
for i in answer_range:
	file_path = dir_path + "answer_" + str(i) + "_3.csv"
	with open(file_path, 'r', encoding='utf-8') as c:
		lines = c.readlines()
	task_name = lines[0].split("_")[0]
	results = lines[1:]
	canvases = list(map(to_canvas, results))

	ogdata_path = os.path.dirname(os.getcwd()) + "/ARCdata/data/training/"
	with open(ogdata_path + task_name + ".json", 'r', encoding="utf-8") as og_json:
		j = json.load(og_json)
	for canvas in canvases:
		j["train"].append({"input": j["test"][0]["input"], "output": canvas})
	with open(os.getcwd() + "/output_json/" + task_name + ".json", 'w') as f:
		json.dump(j, f)
	