import numpy as np
from matplotlib import pyplot as plt
import cv2 as cv2
import tifffile
import PIL
from PIL import Image, ImageEnhance, ImageFilter
import time
import imutils
from array2gif import write_gif

import os
from os import path

from scipy import ndimage as ndi
from scipy.signal import convolve2d as conv2

from skimage import feature, filters, color, data, restoration
from skimage.segmentation import watershed
from skimage.filters import sobel
from skimage.morphology import skeletonize
from skimage.util import invert

import sys
import warnings 

warnings.simplefilter("ignore", ResourceWarning)

data_folders = []
for i in os.listdir("./workspace"):
    data_folders.append(i)

data_files = {}
annotation_files = {}

def segment2(data_folder, annotation_folder):
    for file in os.listdir("./workspace/" + data_folder):
        time_stamp = int(file.split("_")[-1].split(".tif")[0])
        data_files[time_stamp] = file
        
    for file in os.listdir(annotation_folder):
        time_stamp = int(file.split("_")[-1].split(".png")[0])
        annotation_files[time_stamp] = file
        
    tif0 = Image.open(("./workspace/" + data_folder + "/" + data_files[10]))
    # test = np.array(Image.open((annotation_folder + "/" + annotation_files[15])))
    print(tif0.size)
    channels = 2
    nslices = tif0.n_frames / channels
    nframes = len(data_files)
    slice_layer = int(nslices // 2)
    frame_skip = 5

    output_set = []
    original_set = []
    final_set = []
    x_size = tif0.size[0]
    y_size = tif0.size[1]
    x_mid = int(x_size/2)
    y_mid = int(y_size/2)

    frame = 1
    iterations = 0
    # while frame < nframes:
    while frame <= nframes:
        tif = tifffile.TiffFile(("./workspace/" + data_folder + "/" + data_files[frame]))
        
        nucleus_array = tif.pages[(slice_layer)*channels + 1].asarray()
        median = np.median(nucleus_array) 
        nucleus_array = nucleus_array - median
        nucleus_array = nucleus_array/np.max(nucleus_array)*255 # 0-255 scaling
        nucleus_array[nucleus_array<1] = 1
        
        zero_array = np.zeros_like(nucleus_array)

        membrane_array = tif.pages[(slice_layer)*channels].asarray()
        median = np.median(membrane_array)
        membrane_array = membrane_array - median
        membrane_array = np.floor(membrane_array/np.max(membrane_array)*255) # 0-255 scaling
        membrane_array[membrane_array<1] = 1
        membrane_array = membrane_array.astype(np.uint8)
    #     membrane_array = cv2.convertScaleAbs(membrane_array, alpha=3, beta=0)

        annotation = np.array(Image.open((annotation_folder + "/" + annotation_files[iterations])))
        annotation_processed = np.zeros_like(zero_array)
        
        for i in range(y_size):
            for j in range(x_size):
                r, g, b, a = annotation[i][j]
                if r == 255:
                    annotation_processed[i][j] = 1 # add membrane
                elif g == 255:
                    annotation_processed[i][j] = 2 # merge 
                elif b == 255:
                    annotation_processed[i][j] = 3 # delete membrane
                elif r == 128:
                    annotation_processed[i][j] = 4 # add membrane
                elif r == 240:
                    annotation_processed[i][j] = 5 # subtract membrane
            
        membrane_array[annotation_processed == 1] = 255
        membrane_array[annotation_processed == 3] = 1

        img_array = membrane_array
        original_array = membrane_array + nucleus_array
        original_array[original_array > 255] = 255
        
        y_size = img_array.shape[0]
        x_size = img_array.shape[1]
        
        denoise_method = 0

        if denoise_method == 0:
            psf = np.ones((5, 5)) / 25
            denoised_membrane = restoration.richardson_lucy(membrane_array, psf, iterations=10, clip=False)
        elif denoise_method == 1:
            denoised_membrane = cv2.fastNlMeansDenoising(img_array, h=10)

        denoised_membrane = denoised_membrane.astype(np.uint8)
    #     plt.imshow(denoised_membrane, cmap = 'gray')
        
        # Adaptive Thresholding
        th2 = cv2.adaptiveThreshold(membrane_array,255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)

        ### Thresholded Membranes
        membrane_array2 = th2.copy()
        membrane_array2[membrane_array <= 10] = 0
        membrane_array2[denoised_membrane <= 10] = 0
        min_size = 5
        
        membrane2_label, _  = ndi.label(membrane_array2)
        membrane2_id, membrane2_counts = np.unique(membrane2_label, return_counts=True)
        membrane2_id = membrane2_id[membrane2_counts >= min_size]
        
        for i in range(membrane2_label.shape[0]):
            for j in range(membrane2_label.shape[1]):
                if membrane2_label[i][j] in membrane2_id and membrane2_label[i][j] != 0:
                    membrane2_label[i][j] = 255
                else:
                    membrane2_label[i][j] = 0
        
        ### Thresholded Labelled Cells
        cell_array = th2.copy()
        cell_array[membrane_array > 10] = 0
        
        # Labelling & Cleaning (cell)
        min_size = 150
        cell_array_label, _  = ndi.label(cell_array)
        cell_id, counts = np.unique(cell_array_label, return_counts=True)
        cell_id = cell_id[counts >= min_size]

        for i in range(cell_array_label.shape[0]):
            for j in range(cell_array_label.shape[1]):
                if cell_array_label[i][j] in cell_id and cell_array_label[i][j] != 0:
                    cell_array_label[i][j] = 255
                else:
                    cell_array_label[i][j] = 0

        cell_array_label = ndi.binary_fill_holes(cell_array_label)
        cell_array =  cell_array.astype(np.uint8)
        cell_array_clean = cell_array_label.astype(np.uint8)
        
        #     plt.imshow(cv2.addWeighted(cell_array, 0.5, membrane_array2, 1, 0))
        #     plt.imshow(cell_array_clean, cmap = 'gray')

        ### Void detection
        void = np.zeros_like(cell_array_clean)
        void[cell_array_clean == 0] = 1 
        void[cell_array_clean > 0] = 0

        inverse_mask = np.zeros_like(membrane_array2)
        inverse_mask[membrane_array2 <= 10] = 1
        inverse_mask[membrane_array2 >= 10] = 0

        D = ndi.distance_transform_edt(inverse_mask)
        
        D_void = ndi.distance_transform_edt(void)
        D_void[D_void <= 15] = 0 # Retract void to min dist = n away from existing seeds
        D_void[D_void > 0] = D[D_void > 0] # Set void dist to membrane distance
        D_void[D_void < 4] = 0 # Remove weak bridges between membrane distance
        D_void[D_void > 0] = 1
        
        combined_seeds = cell_array_clean + D_void
        seedLabel, _  = ndi.label(combined_seeds)
        
        labels = watershed(-D, seedLabel, compactness=2)
        labels[labels > 0] = labels[labels > 0] + 50
        labels = labels / np.max(labels) * 240
        
        center_label = labels[y_mid][x_mid]

        # Changing labels in accordance to annotations
        merged_center_labels = np.unique(labels[annotation_processed  == 2])
        for i in merged_center_labels:
            labels[labels == i] = center_label
        
        labels[annotation_processed == 4] = center_label
        labels[annotation_processed == 5] = 1

        final_segment = np.zeros_like(membrane_array2)
        final_segment[labels == center_label] = 255
        
        highlight_r = labels.copy().astype(np.uint8)
        highlight_r[labels == center_label] = 255
        highlight_r[membrane_array2 >= 10] = 255
        
        highlight_gb = labels.copy().astype(np.uint8)
        highlight_gb[membrane_array2 >= 10] = 255
        
        
    #     output_b = cv2.addWeighted(labels.astype(np.uint8), 10, membrane_array2.astype(np.uint8), 0.1, 0)
        output_rgb = np.array([highlight_r, highlight_gb, highlight_gb])
        output_set.append(output_rgb)
        
        membrane_array[membrane_array>10] = 255
        nucleus_array[nucleus_array>10] = 255
        
        original_set.append(np.array([membrane_array.astype(np.uint8), nucleus_array.astype(np.uint8), zero_array.astype(np.uint8)]))
        
        final_rgb = np.array([final_segment, final_segment, final_segment])
        final_set.append(final_rgb)

        if frame % 10 == 0:
            print(frame)
        frame += frame_skip
        iterations += 1

    
    file_output_name = data_folder.split("\\")[-1].split("/")[-1]
    write_gif(output_set, "./raw/" + file_output_name + "_raw.gif", fps=1)
    write_gif(final_set, "./processed/" + file_output_name + "_processed.gif", fps=1)
    print("Round 2 Auto segmentation complete for: " + file_output_name)

fol_num = 0
for data_folder in data_folders:
    fol_num += 1
    file_output_name = data_folder.split("\\")[-1].split("/")[-1]
    print("Job {}/{}: ".format(fol_num, len(data_folders)), file_output_name)
    annotation_folder = "./temp/{}".format(file_output_name + "_raw.gif")
    if path.exists(annotation_folder):
        segment2(data_folder, annotation_folder)
    else:
        print("Annotation path does not exist.")