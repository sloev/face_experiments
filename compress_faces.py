
from imutils import face_utils
import imutils
import numpy as np
import collections
import dlib
import cv2
from tqdm import tqdm
import os

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('landmarks.dat')

dir_in = "video_frames/"
dir_out = "output_frames/"

def add_faces(image, background):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 1)
    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        #initialize mask array
        remapped_shape = np.zeros_like(shape) 
        feature_mask = np.zeros((image.shape[0], image.shape[1]))   

        # we extract the face
        remapped_shape = cv2.convexHull(shape)
        cv2.fillConvexPoly(feature_mask, remapped_shape[0:27], 1)
        feature_mask = feature_mask.astype(np.bool)
        background[feature_mask] = image[feature_mask]

background = None
for filename in tqdm(sorted(os.listdir(dir_in))):
    if not filename.endswith(".jpg"):
        continue
    print("processing ", filename, flush=True)
    image = cv2.imread(dir_in + filename)
    if background is None:
        background = np.zeros_like(image)
    add_faces(image, background)
    cv2.imwrite(dir_out + filename, background)


