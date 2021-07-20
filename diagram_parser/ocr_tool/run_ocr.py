#!/usr/bin/env python3

import mathpix
import json
import os
import time
#
# Simple example of calling Mathpix OCR with ../images/algebra.jpg.
#
# We use the default ocr (math-only) and a single return format, latex_simplified.
#
# If you expect the image to be math and want to examine the result
# as math then the return format should either be latex_simplified,
# asciimath, or mathml. If you want to see the text in the image then
# you should include 'ocr': ['math', 'text'] as an argument and
# the return format should be either text or latex_styled
# (depending on whether you want to use the result as a paragraph or an equation).
#

folder = '../detection_results/ocr_results'
sub_folders = os.listdir(folder)

for sub_folder in sub_folders:
    files = os.listdir(os.path.join(folder, sub_folder))
    files = list(filter(lambda x: x.endswith('jpg'), files))
    
    for file in files:
        path = os.path.join(folder, sub_folder, file)
        r = mathpix.latex({
            'src': mathpix.image_uri(path),
            'formats': ['latex_simplified']
        })
        res = json.dumps(r, indent=4, sort_keys=True)
        # print(res['latex_simplified'])

        id = os.path.splitext(file)[0]
        with open(os.path.join(folder, sub_folder, id+'.json'), 'w') as f:
            f.write(res)
        print(os.path.join(folder, sub_folder, id+'.json'))
        
        time.sleep(1.5)

