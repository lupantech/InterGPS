import os

for i in range(0, 70):
    print()
    print()
    print (i)
    os.system("python csv_validation.py --csv_annotations_path geometry_labels_val.csv --model_path csv_retinanet_" + str(i) + ".pt  --images_path new_symbols --class_list_path classes.txt")

