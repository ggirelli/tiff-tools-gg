#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# 
# Author: Gabriele Girelli
# Email: gigi.ga90@gmail.com
# Version: 0.0.1
# Date: 20180302
# Project: bioimaging
# Description: Uncompress compressed tiff.
# Requires: 
# 
# Changelog:
#  v0.0.1 - 20171205: first implementation.
# 
# ------------------------------------------------------------------------------



# DEPENDENCIES =================================================================

import argparse
from joblib import Parallel, delayed
import multiprocessing
import numpy as np
import os
import re
from scipy import ndimage as ndi
from skimage.filters import threshold_local, threshold_otsu
import skimage.io as io
from skimage.measure import label
from skimage.morphology import closing, cube, square
from skimage.segmentation import clear_border
import sys
import tifffile
import warnings

# PARAMETERS ===================================================================

# Add script description
parser = argparse.ArgumentParser(description = '''
Uncompress all tiff files matching the specified pattern.
''')

# Add mandatory arguments
parser.add_argument('imgFolder', type = str, nargs = 1,
    help = 'Path to folder containing deconvolved tiff images.')
parser.add_argument('outFolder', type = str, nargs = 1,
    help = '''Path to output folder where binarized images will be stored
    (created if does not exist).''')

# Optional parameters
default_inreg = '^.*\.tiff?$'
parser.add_argument('--inreg', type = str, nargs = 1,
    help = """regular expression to identify images from imgFolder.
    Default: '%s'""" % (default_inreg,), default = [default_inreg])
parser.add_argument('--threads', type = int, nargs = 1,
    help = """number of threads for parallelization. Default: 1""",
    default = [1])

# Version flag
version = "0.0.1"
parser.add_argument('--version', action = 'version',
    version = '%s %s' % (sys.argv[0], version,))

# Parse arguments
args = parser.parse_args()

# Assign to in-script variables
imgdir = args.imgFolder[0]
outdir = args.outFolder[0]
inpattern = re.compile(args.inreg[0])
ncores = args.threads[0]

# Additional checks
maxncores = multiprocessing.cpu_count()
if maxncores < ncores:
    print("Lowered number of threads to maximum available: %d" % (maxncores))
    ncores = maxncores

# FUNCTIONS ====================================================================

def add_trailing_slash(s):
    # Add OS-specific folder separator if missing
    # 
    # Args:
    #   s (string): path to folder.
    # 
    # Returnsç
    #   string: fixed path to folder.
    if not os.sep == s[-1]:
        return(s + os.sep)
    else:
        return(s)

def autoselect_time_frame(im):
    # Selects the first non-empty time frame found.
    #
    # Args:
    #     im (np.array): image.

    # Select time frame if TZYX or ZYXT
    if 4 == len(im.shape):
        # TZYX
        if im.shape[0] == 1:
            return(im)
        
        #ZYXT
        selected = None
        if 4 == len(im.shape):
            for i in range(im.shape[3]):
                if 0 != im[:, :, :, i].max():
                    selected = i
                    break
        return(im[:, :, :, selected])
    else:
        return(im)

def slice_k_d_img(img, k):
    # Select one k-d image from a n-d image.
    # 
    # Note:
    #     n >= k
    # 
    # Args:
    #     img (np.array): image.
    #     k (int): number of dimensions to keep.
    # 
    # Returns:
    #     np.array: k-d image.

    # Check that k is lower than or equal to n
    if k > len(img.shape):
        return(img)

    # Slice image
    idxs = [(0,) for i in range(len(img.shape) - k)]
    for i in range(k):
        idxs.append(tuple(range(img.shape[len(img.shape) - k + i])))
    img = img[np.ix_(*idxs)].reshape(img.shape[len(img.shape) - k:])

    # Output
    return(img)

def get_dtype(i):
    '''
    Identify bit depth for a matrix of maximum intensity i.
    '''
    depths = [1, 2, 4, 8, 16]
    for depth in depths:
        if i <= 2**depth-1:
            return("u%d" % (depth,))
    return("u")

def save_tif(path, img, dtype, compressed):
    new_shape = [1]
    [new_shape.append(n) for n in img.shape]
    img.shape = new_shape

    if compressed:
        tifffile.imsave(path, img.astype(dtype),
            shape = img.shape, compress = 9,
            dtype = dtype, imagej = True, metadata = {'axes' : 'CZYX'})
    else:
        tifffile.imsave(path, img.astype(dtype),
            shape = img.shape, compress = 0,
            dtype = dtype, imagej = True, metadata = {'axes' : 'CZYX'})

def uncompress(imgpath, imgdir):
    # Perform 3D segmentation of nuclear staining image.
    # 
    # Args:
    #   imgpath (string): input image file name.
    #   imgdir (string): input image folder.
    # 
    # Returns:
    #   string: path to output image.
    
    # Preparation --------------------------------------------------------------

    # Read image
    img = tifffile.imread(os.path.join(imgdir, imgpath))

    # Write image
    save_tif(os.path.join(outdir, imgpath), img, 'uint8', False)

    return(os.path.join(outdir, imgpath))

# RUN ==========================================================================

# Add trailing slashes
imgdir = add_trailing_slash(imgdir)
outdir = add_trailing_slash(outdir)

# Stop if input folder does not exist
if not os.path.isdir(imgdir):
    sys.exit("!ERROR! Image folder not found: %s" % (imgdir,))

# Create output folder
if not os.path.isdir(outdir):
    os.mkdir(outdir)

# Identify images --------------------------------------------------------------

# Identify tiff images
imglist = [f for f in os.listdir(imgdir) 
    if os.path.isfile(os.path.join(imgdir, f))
    and not type(None) == type(re.match(inpattern, f))]

# Start iteration --------------------------------------------------------------

outlist = Parallel(n_jobs = ncores)(
    delayed(uncompress)(imgpath, imgdir)
    for imgpath in imglist)

# END ==========================================================================

################################################################################
