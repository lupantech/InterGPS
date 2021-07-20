## 给预测的序列加随机序号

import json
import random
from numpy.random import seed

seed(1234)
random.seed(1234)

# input_file = '../results/test/pred_seq_result_bart_epoch19_seq5.json'
# output_file = '../results/test/pred_seq_result_bart_epoch19_seq5_add_random.json'
input_file = '../results/test/pred_seqs_test_bart_best.json'
output_file = '../results/test/pred_seqs_test_bart_best_add_random.json'
input = json.load(open(input_file))

output = {}
for pid, data in input.items():
    new_seq = data['seq'][0] + random.sample(list(range(1,18))*10, 100)
    output[pid] = {'id':pid, 'num_seqs':1, 'seq':new_seq}
    
## Save result.json file
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2, separators=(',', ': '))

