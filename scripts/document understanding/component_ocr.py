import pandas as pd
import numpy as np
import cv2


# exemplars = pd.read_csv('/home/brian/Downloads/exemplars.csv', index_col=None)
# embeddings = exemplars.values[:, :-2].astype(float)
# character_map = exemplars.character.to_dict()


def standardize_binary_image(image, dim=16):
   scaled_image = cv2.resize(image.astype('uint8'), dsize=(dim, dim), interpolation=cv2.INTER_LINEAR)
   flat_image = np.ravel(scaled_image) / 255
   return -1 + 2 * flat_image


def predict_character(component_image):
    image = standardize_binary_image(component_image)
    scores = embeddings @ image
    # ToDo: return full result per-character?
    character_index = scores.argmax().item()
    return character_map[character_index], scores[character_index].item() / 256








