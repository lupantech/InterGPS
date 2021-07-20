import os
import json

INPUT_PATH = '../results/train/splits'
OUTPUT_PATH = '../results/train'

# read all the 100 result json files
prob2sol = {}
for name in os.listdir(INPUT_PATH):
    path = os.path.join(INPUT_PATH, name)
    js = json.load(open(path, "r"))
    for pid, res in js.items():
        if res["status"] != "correct":
            continue
        if pid not in prob2sol:
            prob2sol[pid] = {"num":0, "seqs":[]}
        if res["seq"] not in prob2sol[pid]['seqs']:
            prob2sol[pid]['seqs'].append(res["seq"])

# merge results into one file
prob2sol = dict(sorted(prob2sol.items(), key=lambda x:x[0])) # sort the problem id
for pid, res in prob2sol.items():
    prob2sol[pid]['num'] = len(res['seqs'])
    prob2sol[pid]['seqs'] = sorted(res['seqs'], key = lambda x:len(x))

print(prob2sol["100"])
print("\n{} problems in 2401 have correct theorem seqs".format(len(prob2sol.keys())))
json.dump(prob2sol, open(OUTPUT_PATH + "/pred_seqs_train_merged_correct.json", "w"), indent = 2)

