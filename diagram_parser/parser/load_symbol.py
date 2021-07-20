import os
import cv2
import json

def get_real_label(latex_text):
    '''
    filter out unnecessary symbols in latex text
    '''
    def erase_unnecessary_latex(latex_text):
        unnecessary_list = ['\\mathcal', '\\boldsymbol', '\\mathrm', '\\mathbf', "\operatorname"]
        for phrase in unnecessary_list:
            pos = latex_text.find(phrase)
            if pos != -1:
                right_brace = pos + latex_text[pos:].find('}')
                return latex_text[0 : pos] + latex_text[pos+len(phrase)+1 : right_brace] + latex_text[right_brace+1 : ]
        return latex_text
    
    latex_text = latex_text.replace(' ', '')
    while latex_text != erase_unnecessary_latex(latex_text):
        latex_text = erase_unnecessary_latex(latex_text)
    latex_text = latex_text.replace("\\left", "").replace("\\right", "")
    latex_text = latex_text.replace("\\ell", "l")
    latex_text = latex_text.replace("\\times", "")  # impossible
    latex_text = latex_text.strip('.').strip('(').strip(')')
    return latex_text

    
def modify(now):
    '''
    fix the latex text
    '''
    now = ''.join(now.split()) # add
    if now == "": return now
    if now.find("^{\circ}") != -1: return now
    if len(now) > 3 and now[-4] == "^" and now[-3] == "{" and now[-1] == "}":
        return now[0:-4] + "^{\circ}"
    if ')' in now and not '(' in now:
        now = '(' + now
    if now[-1] == ".": now = now[0: -1]
    if len(now) == 1 or now.isalpha(): return now
    units = ["km", "yd", "in", "in^{2}", "yd^{2}", "ft", "m", "mm^{2}", "mm", "c"]
    for unit in units:
        if now.endswith(unit):
            now = now.replace(unit, "")
    return now.strip()


def load_symbol(problem_list, ocr_path, box_path):
    ocr_results = {}
    sign_results = {}
    size_results = {}
    for name in problem_list:
        ocr_results[name] = []
        sign_results[name] = []
        size_results[name] = None
        
        current_path = os.path.join(ocr_path, name)
        if not os.path.exists(current_path):
            print ("Can not find the mathpix result:", current_path)
        else:
            tex_list = set([x.split('.')[0] for x in os.listdir(current_path)])
            #print (tex_list)
            for tex_id in tex_list:
                with open(os.path.join(current_path, tex_id + ".txt"), "r") as f:
                    position = tuple(map(int, f.readline().split(',')[:-1]))
                #print (position, os.path.join(current_path, tex_id + ".json"))
                with open(os.path.join(current_path, tex_id + ".json"), "r") as f:
                    mathpix = json.load(f)
                
                label = ""
                if 'data' in mathpix and type(mathpix['data']) in [list, tuple] and len(mathpix['data']) > 0:
                    label = get_real_label(mathpix['data'][1]['value'])
                elif 'latex_simplified' in mathpix:
                    label = mathpix['latex_simplified']
                elif 'text' in mathpix:
                    label = mathpix['text']
                else:
                    print("can not read ocr result:", os.path.join(current_path, tex_id))
                label = modify(label)
                if label != "":
                    ocr_results[name].append(position + (label, ))
        
        if not os.path.exists(os.path.join(box_path, name + ".txt")):
            print ("Can not find the box file:", name)
        else:
            with open(os.path.join(box_path, name + ".txt"), "r") as f:
                for data in f.readlines():
                    if data.strip() == "":
                        continue
                    type_ = data.strip().split(',')[-1]
                    if type_!= 'text':
                        sign = tuple(map(int, data.split(',')[:-1])) + (type_, )
                        sign_results[name].append(sign)
            if os.path.exists(os.path.join(box_path, name + ".jpg")):
                size_results[name] = cv2.imread(os.path.join(box_path, name + ".jpg")).shape[0:2]
            elif os.path.exists(os.path.join(box_path, name + "_modified.jpg")):
                size_results[name] = cv2.imread(os.path.join(box_path, name + "_modified.jpg")).shape[0:2]
    return ocr_results, sign_results, size_results


