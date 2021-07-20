from scipy import ndimage
import cv2
import numpy as np

from geosolver.diagram.states import ImageSegment, ImageSegmentParse
from geosolver.ontology.instantiator_definitions import instantiators

__author__ = 'minjoon'


def parse_image_segments(image):
    kernel = np.ones((3,3), np.uint8)
    block_size = 13
    c = 20
    min_area = 20
    min_height = 3
    min_width = 3

    image_segments = _get_image_segments(image, kernel, block_size, c)
    diagram_segment, label_segments = _get_diagram_and_label_segments(image_segments, min_area, min_height, min_width)
    image_segment_parse = ImageSegmentParse(image, diagram_segment, label_segments)
    return image_segment_parse


def _get_image_segments(image, kernel, block_size, c):
    
    binarized_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, block_size, c)

    labeled, nr_objects = ndimage.label(binarized_image, structure=kernel)
    slices = ndimage.find_objects(labeled)

    image_segments = {}
    for idx, slice_ in enumerate(slices):
        offset = instantiators['point'](slice_[1].start, slice_[0].start)
        sliced_image = image[slice_]
        boolean_array = labeled[slice_] == (idx+1)
        segmented_image = 255- (255-sliced_image) * boolean_array
        pixels = set(instantiators['point'](x, y) for x, y in np.transpose(np.nonzero(np.transpose(boolean_array))))
        binarized_segmented_image = cv2.adaptiveThreshold(segmented_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                          cv2.THRESH_BINARY_INV, block_size, c)
        #scale_factor = 5
        #scaled_img = cv2.resize(segmented_image, (0,0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        #thres,binarized_segmented_image = cv2.threshold(scaled_img, 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        
        image_segment = ImageSegment(segmented_image, sliced_image, binarized_segmented_image, pixels, offset, idx)
        image_segments[idx] = image_segment

    return image_segments

'''def _union(self, diagram, image):
    diagram.shape[0] = max(diagram.shape[0], diagram.offset.x - image.offset.x + image.shape[0])
    diagram.shape[1] = max(diagram.shape[1], diagram.offset.x - image.offset.x + image.shape[0])
    diagram.offset.x = min(diagram.offset.x, image.offset.x)
    diagram.offset.y = min(diagram.offset.y, image.offset.y)
    diagram.pixels = diagram.pixels | image.pixels'''
    

def _get_diagram_and_label_segments(image_segments, min_area, min_height, min_width):
    '''Erase the max area (padding)
    diagram_segment = max(image_segments.values(), key=lambda s: s.area)
    d = list(image_segments.values())
    d.remove(diagram_segment)
    '''
    diagram_segment = max(image_segments.values(), key=lambda s: s.area)
    union_to_diagram = []

    label_segments = {}
    for key, image_segment in image_segments.items():
        if key == diagram_segment.key:
            continue
        a = image_segment.area >= min_area
        h = image_segment.shape[1] >= min_height
        w = image_segment.shape[0] >= min_width
        if a and h and w:
            '''if image_segment.area * 2 >= diagram_segment.area:
                union_to_diagram.append(image_segment)
            else:'''
            label_segments[key] = image_segment
    
    #for image_segment in union_to_diagram:
    #    self._union(diagram_segment, image_segment)

    return diagram_segment, label_segments
