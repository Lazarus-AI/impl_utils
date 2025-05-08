import cv2
import numpy as np
from component_ocr import predict_character


class Components:
    def __init__(self, binary_image):
        self.num_components, self.mask, self.stats, self.centroids = cv2.connectedComponentsWithStats(binary_image)
        # done in numpy for speed...
        self.scale = self.stats[:, [2, 3]].max(axis=1)
        self.density = 100 * self.stats[:, -1] / (self.stats[:, 2] * self.stats[:, 3])
        self.left = self.stats[:, 0]
        self.top = self.stats[:, 1]
        self.width = self.stats[:, 2]
        self.height = self.stats[:, 3]
        self.area = self.stats[:, 4]
        self.right = self.left + self.width
        self.bottom = self.top + self.height
        self.aspect_ratio = self.width / self.height
        self.components = self.__make_component_dicts()


    def __make_component_dicts(self):
        components = np.hstack([self.stats, self.right[..., np.newaxis], self.bottom[..., np.newaxis], self.density[..., np.newaxis], self.scale[..., np.newaxis]])
        keys = ['left', 'top', 'width', 'height', 'area', 'right', 'bottom', 'density', 'scale']
        components_tmp = [dict(zip(keys, row)) for row in components.astype('int')]  # this results in non-serializable numpy int64
        for index, c in enumerate(components_tmp):
            for key, val in c.items():
                c[key] = int(val)
            c['index'] = index
        return components_tmp

    def ocr(self, component_indices):
        for index in component_indices.tolist():
            data = self.components[index]
            component_window = self.mask[data['top']:data['bottom'], data['left']:data['right']]
            component_binary_image = np.where(component_window == index, 255, 0)
            self.components[index]['ocr'] = predict_character(component_binary_image)

