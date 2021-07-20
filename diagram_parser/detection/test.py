import torch
import shutil
import numpy as np
import time
import os
import csv
import cv2
import argparse
from tqdm import tqdm


def load_classes(csv_reader):
    result = {}

    for line, row in enumerate(csv_reader):
        line += 1

        try:
            class_name, class_id = row
        except ValueError:
            raise (ValueError('line {}: format should be \'class_name,class_id\''.format(line)))
        class_id = int(class_id)

        if class_name in result:
            raise ValueError('line {}: duplicate class name: \'{}\''.format(line, class_name))
        result[class_name] = class_id
    return result


# Draws a caption above the box in an image
def draw_caption(image, box, caption):
    b = np.array(box).astype(int)
    cv2.putText(image, caption, (b[0], b[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 2)
    cv2.putText(image, caption, (b[0], b[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)


def detect_image(image_path, model_path, class_list, output_path):
    with open(class_list, 'r') as f:
        classes = load_classes(csv.reader(f, delimiter=','))

    labels = {}
    for key, value in classes.items():
        labels[value] = key

    model = torch.load(model_path)

    if torch.cuda.is_available():
        model = model.cuda()

    model.training = False
    model.eval()
    cnt = 0
    test_set = list(range(2401, 3002))

    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(os.path.join(output_path, 'box_results'))
    os.makedirs(os.path.join(output_path, 'ocr_results'))

    for img_name in tqdm(os.listdir(image_path)):
        if not img_name.endswith(".png") and not img_name.endswith(".jpg"):
            continue
        image_id = os.path.splitext(img_name)[0]
        try:
            if int(image_id) not in test_set:
                continue
        except:
            continue

        ocr_folder = os.path.join(output_path, 'ocr_results', image_id)
        os.makedirs(ocr_folder)

        box_folder = os.path.join(output_path, 'box_results')
        box_txt_path = os.path.join(box_folder, image_id + ".txt")
        box_vis_path = os.path.join(box_folder, image_id + "_modified.jpg")

        image = cv2.imread(os.path.join(image_path, img_name))
        if image is None:
            print(os.path.join(image_path, img_name))
            print("Error! Can not read image", image_id)
            continue
        image_orig = image.copy()
        no_modify = image_orig.copy()

        rows, cols, cns = image.shape
        smallest_side = min(rows, cols)

        # rescale the image so the smallest side is min_side
        min_side = 608
        max_side = 1024
        scale = min_side / smallest_side

        # check if the largest side is now greater than max_side, which can happen
        # when images have a large aspect ratio
        largest_side = max(rows, cols)

        if largest_side * scale > max_side:
            scale = max_side / largest_side

        # resize the image with the computed scale
        image = cv2.resize(image, (int(round(cols * scale)), int(round((rows * scale)))))
        rows, cols, cns = image.shape

        pad_w = 32 - rows % 32
        pad_h = 32 - cols % 32

        new_image = np.zeros((rows + pad_w, cols + pad_h, cns)).astype(np.float32)
        new_image[:rows, :cols, :] = image.astype(np.float32)
        image = new_image.astype(np.float32)
        image /= 255
        image -= [0.485, 0.456, 0.406]
        image /= [0.229, 0.224, 0.225]
        image = np.expand_dims(image, 0)
        image = np.transpose(image, (0, 3, 1, 2))

        with torch.no_grad():
            image = torch.from_numpy(image)
            if torch.cuda.is_available():
                image = image.cuda()

            st = time.time()
            # print(image.shape, image_orig.shape, scale)
            scores, classification, transformed_anchors = model(image.cuda().float())
            # print('Elapsed time: {}'.format(time.time() - st))
            idxs = np.where(scores.cpu() > 0.5)
            img_name = os.path.join(image_path, img_name)

            box_txt_file = open(box_txt_path, 'w')

            for j in range(idxs[0].shape[0]):
                bbox = transformed_anchors[idxs[0][j], :]

                x1 = int(bbox[0] / scale)
                y1 = int(bbox[1] / scale)
                x2 = int(bbox[2] / scale)
                y2 = int(bbox[3] / scale)

                crop_img = no_modify[y1:y1 + (y2 - y1), x1:x1 + (x2 - x1)]
                label_name = labels[int(classification[idxs[0][j]])]
                # if label_name != 'text':
                #     continue
                # print(label_name)
                # print(bbox, classification.shape)

                score = scores[j]
                caption = '{} {:.3f}'.format(label_name, score)
                # draw_caption(img, (x1, y1, x2, y2), label_name)
                print(x1, y1, x2, y2, label_name, sep=',', file=box_txt_file)
                draw_caption(image_orig, (x1, y1, x2, y2), caption)
                cv2.rectangle(image_orig, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=2)

                if label_name != "text": continue

                full_path = os.path.join(ocr_folder, str(cnt))
                cv2.imwrite(full_path + '.jpg', crop_img)
                with open(full_path + '.txt', 'w') as f2:
                    print(x1, y1, x2, y2, label_name, sep=',', file=f2)
                cnt += 1

            cv2.imwrite(box_vis_path, image_orig)
            box_txt_file.close()
            # cv2.imshow('detections', image_orig)
            # cv2.waitKey(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple script for visualizing result of training.')

    parser.add_argument('--image_dir', help='Path to directory containing images')
    parser.add_argument('--model_path', help='Path to model')
    parser.add_argument('--class_list', help='Path to CSV file listing class names')
    parser.add_argument('--output_path', help='Path to save box detection results and ocr results')

    parser = parser.parse_args()

    detect_image(parser.image_dir, parser.model_path, parser.class_list, parser.output_path)
