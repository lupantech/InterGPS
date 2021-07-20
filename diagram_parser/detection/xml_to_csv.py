import os
import glob
import pandas as pd
import xml.etree.ElementTree as ET
import json
import imagehash
from PIL import Image
hash = set() 

def xml_to_csv(path, annos_ids, use_hash = True):
    xml_list = []
    classes = set()
    for xml_file in glob.glob(path + '/*.xml'):
        ids = os.path.basename(xml_file).split('.')[0]
        if ids not in annos_ids:
            continue
        ids = ids + ".png"
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        if use_hash:
            h = imagehash.average_hash(Image.open(path + '/' +  ids))
            if h in hash:
                continue
            else:
                hash.add(h)

        for member in root.findall('object'):
            if member[0].text == 'head' or member[0].text == 'tail' or member[0].text == 'point' or member[0].text == 'arrow':
                continue
            if member[0].text == 'penta angle' or member[0].text == 'quad angle' or member[0].text == 'quadruple bar' \
             or member[0].text == 'quintuple angle' or member[0].text == 'quadruple angle':
                continue
            
            if member[0].text == 'test':
                member[0].text = 'text'

            if member[0].text == 'pendicular' or member[0].text == 'perpedicular':
                member[0].text = 'perpendicular'
            value = (path + '/' +  ids,
                     # int(root.find('size')[0].text),
                     # int(root.find('size')[1].text),
                     int(member[4][0].text),
                     int(member[4][1].text),
                     int(member[4][2].text),
                     int(member[4][3].text),
                     member[0].text
                      )
            classes.add(member[0].text)
            xml_list.append(value)

    column_name = ['filename', 'xmin', 'ymin', 'xmax', 'ymax', 'class']
    xml_df = pd.DataFrame(xml_list, columns=column_name)
    classes = list(classes)
    classes.sort()
    print(classes)
    return xml_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple script to make training and testing csv files.')
    
    parser.add_argument('--annotated_path', help='Path to save box detection results and ocr results', default="../data/geometry3k/symbols")

    parser = parser.parse_args()

    train_annos_ids = []
    val_annos_ids = []
    for i in range(0, 2401):
        train_annos_ids.append(str(i))

    for i in range(2401, 3002):
        val_annos_ids.append(str(i))


    xml_df = xml_to_csv(parser.annotated_path, val_annos_ids, use_hash=False)
    xml_df.to_csv('geometry_labels_val.csv', index=None, header=False)
    
    xml_df = xml_to_csv(parser.annotated_path, train_annos_ids, use_hash=True)
    xml_df.to_csv('geometry_labels.csv', index=None, header=False)
    print('Successfully converted xml to csv.')


