#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# 
# Author: Gabriele Girelli
# Email: gigi.ga90@gmail.com
# Version: 0.0.1
# Date: 20171205
# Project: bioimaging
# Description: automatic 3D segmentation of nuclear staining.
# Requires: 
# 
# Changelog:
#  v0.0.1 - 20171205: first implementation.
# 
# ------------------------------------------------------------------------------



# DEPENDENCIES =================================================================

import argparse
from joblib import Parallel, delayed
import math
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
import warnings

# PARAMETERS ===================================================================

# Add script description
parser = argparse.ArgumentParser(description = '''
Perform automatic 3D segmentation of DNA staining. Images are first identified
based on a regular expression matching the file name. Then, they are first
re-scaled if deconvolved with Huygens software, then a global (Otsu) and
local (median) thresholds are combined to binarize the image in 3D. Then, holes
are filled in 3D and a closing operation is performed to remove small objects.
Objects are filtered based on volume and Z size, and those touching the XY
contour of the image are discarded. The generated images have identified objects
labeled with different intensity levels.
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
parser.add_argument('--outprefix', type = str, nargs = 1,
    help = """prefix to add to the name of output binarized images.
    Default: 'mask_'""", default = ['mask_'])
parser.add_argument('--neighbour', type = int, nargs = 1,
    help = """Side of neighbourhood square/cube. Default: 101""",
    default = [101])
parser.add_argument('--radius', type = float, nargs = 2,
    help = """Range of object radii [vx] to be considered a nucleus.
    Default: [10, Inf]""", default = [10., float('Inf')])
parser.add_argument('--minZ', type = float, nargs = 1,
    help = """Minimum fraction of stack occupied by an object to be considered a
    nucleus. Default: .25""", default = [.25])
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
outprefix = args.outprefix[0]
neighbour_side = args.neighbour[0]
min_z_size = args.minZ[0]
radius_interval = [args.radius[0], args.radius[1]]
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

def get_rescaling_factor(imgpath, imgdir):
    # Get rescaling factor for deconvolved.
    # 
    # Args:
    #     imgpath (string):
    #     imgdir (string):
    # 
    # Returns:
    #     float: scaling factor

    # Build proper path to the deconvolution log file
    symb = re.sub(re.compile("(.*)_cmle.tiff?"), r"\1", imgpath)
    txtpath = symb + "_hystory.txt"
    
    if not os.path.exists(txtpath):
        # Image was not deconvolved
        factor = 1
    else:
        # Identify line with scaling factor
        fhistory = open(txtpath, 'r')
        frows = fhistory.readlines()
        fhistory.close()

        # Retrieve factor
        needle = 'Stretched to Integer type'
        factor = [x for x in frows if needle in x]
        if 0 == len(factor):
            factor = 1
        else:
            factor = factor[0].strip().split(' ')
            factor = float(factor[len(factor) - 1])

    # Output
    return(factor)

def binarize(img, thr):
    # Binarize an image using the provided threshold.
    # 
    # Args:
    #     img (np.array): image.
    #     thr (float or int): intensity threshold.
    # 
    # Returns:
    #     np.array: thresholded image.

    if 2 == len(img.shape):
        img = closing(img > thr, square(3))
    elif 3 == len(img.shape):
        img = closing(img > thr, cube(3))
    return(img)

def threshold_adaptive(img, block_size):
    # Adaptive threshold.
    # 
    # Args:
    #     img (np.array): image.
    #     block_size (int): neighbourhood, if even then it is incremented by 1.
    # 
    # Returns:
    #     np.array: thresholded image.

    # Increment neighbourhood size
    if 0 == block_size % 2:
        block_size += 1

    # Local threshold mask
    lmask = np.zeros(img.shape)

    # Apply threshold per slice
    if 3 == len(img.shape):
        for slice_id in range(img.shape[0]):
            lmask[slice_id, :, :] = threshold_local(
                img[slice_id, :, :], block_size)
        lmask = closing(lmask, cube(3))
    else:
        lmask = threshold_local(i, block_size)
        lmask = closing(lmask, square(3))

    # Output
    return(lmask)

def clear_borders(img, clean_z = None):
    # Remove objects touching the borders of the image.
    # 
    # Args:
    #     img (np.array): image.
    #     clean_z (bool): True to remove the objects touching the Z borders.
    # 
    # Returns:
    #     np.array: cleaned image.

    if 2 == len(img.shape):
        img = clear_border(img)
    elif 3 == len(img.shape):
        for slide_id in range(img.shape[0]):
            img[slide_id, :, :] = clear_border(img[slide_id, :, :])
        if True == clean_z:
            for slide_id in range(img.shape[1]):
                img[:, slide_id, :] = clear_border(img[:, slide_id, :])
    return(img)

def r_to_size(r_interval, do3d):
    # Convert radius interval to size (Area/Volume) interval.
    # 
    # Args:
    #     r_interval (tuple[float]): radius interval.
    #     do3d (bool): calculate sphere volume instead of circle area.
    # 
    # Returns:
    #     tuple(float): size (volume of area) interval.

    if do3d:
        # Volume interval
        o_interval = (4 / float(3)) * np.pi
        o_interval *= np.power(np.array(r_interval), 3)
    else:
        # Area interval
        o_interval = np.pi * np.square(np.array(r_interval))

    return(o_interval)

def uniquec(l):
    # Count the instances of the uniqued integers in l.
    # 
    # Args:
    #     l (list[int]): list of integers.
    # 
    # Returns:
    #     list[tuple]: list of (n, count(n)) for every n in unique(l).

    # Possible integer values
    possible = range(max(l) + 1)

    # Count elements occurrences
    counts = [0 for i in possible]
    for n in l:
        counts[n] += 1

    # Return tupled counts
    return [(i, counts[i]) for i in possible if counts[i]]

def get_objects_xysize(L):
    # Retrieve objects size (2/3D).
    # 
    # Args:
    #     L (np.array): labelled thresholded image.
    # 
    # Returns:
    #     list: XY size of every object in the labelled image.

    Larray = L.reshape([np.prod(L.shape)]).tolist()
    sizes = [t[1] for t in uniquec(Larray) if t[0] != 0]
    return(sizes)

def rm_from_mask(L, torm):
    # Remove elements from a mask.
    # 
    # Args:
    #     L (np.array[int]): labelled objects.
    #     torm (list): list of objects indexes (to remove).

    if len(torm) <= L.max() - len(torm):
        # Update list of objects to be discarded
        torm = [e + 1  for e in torm]

        # Identify which objects to discard
        rm_mask = np.vectorize(lambda x: x in torm)(L)

        # Discard and re-label
        L[rm_mask] = 0
    else:
        # Select objects to be kept
        tokeep = [e + 1 for e in range(L.max()) if not e in torm]

        # Identify which objects to discard
        rm_mask = np.vectorize(lambda x: not x in tokeep)(L)

        # Discard and re-label
        L[rm_mask] = 0

    # Output
    return(L > 0)

def filter_obj_XY_size(mask, radius_interval):
    # Filter objects XY size.
    # 
    # Note:
    #     Uses radius_interval to filter the objects in the provided
    #     mask based on the number of dimensions in mask.
    # 
    # Args:
    #     mask (np.array): binary image
    # 
    # Returns:
    #     tuple: filtered binary image and log string

    # From radius to size
    sinter = r_to_size(radius_interval, 3 == len(mask.shape))

    # Identify objects XY size
    L = label(mask)
    xysizes = get_objects_xysize(L)
    
    # Select objects to be discarded
    torm = np.logical_or(xysizes < sinter[0], xysizes > sinter[1])
    torm = [ii for ii, x in enumerate(torm) if x]

    # Remove objects outside of size interval
    mask = rm_from_mask(L, torm)
    L = label(mask)

    # Output
    return(mask)

def get_objects_zsize(L):
    # Retrieve objects size (2/3D).
    # 
    # Args:
    #     L (np.array): labelled thresholded image.
    # 
    # Returns:
    #     list: Z size of every object in the labelled image.

    sizes = [(L == i).astype('int').sum(0).max() for i in range(1, L.max())]
    return(sizes)

def filter_obj_Z_size(mask, min_z_size):
    # Filter objects Z size.
    # 
    # Note:
    #     Uses min_z_size to filter the objects in the provided mask.
    # 
    # Args:
    #     mask (np.array): binary image
    # 
    # Returns:
    #     tuple: filtered binary image and log string

    # If not a stack, return the mask
    if 3 > len(mask.shape):
        return((mask, log))

    # Check provided conditions
    doFilterZsize = 0 != int(math.ceil(min_z_size))
    doFilterZsize = doFilterZsize and 3 == len(mask.shape)
    if not doFilterZsize:
        return((mask, log))

    # From size to number of slices
    if min_z_size > 1:
        min_z_size = int(math.ceil(min_z_size))
    else:
        min_z_size = min_z_size * mask.shape[0]
        min_z_size = int(math.ceil(min_z_size))

    # Identify objects Z size
    L = label(mask)
    zsizes = get_objects_zsize(L)
    
    # Select objects to be discarded
    torm = np.array(zsizes) < min_z_size
    torm = [ii for ii, x in enumerate(torm) if x]

    # Remove objects lower than minimum size
    mask = rm_from_mask(L, torm)
    L = label(mask)

    # Output
    return(mask)

def run_segmentation(imgpath, imgdir):
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
    img = io.imread(os.path.join(imgdir, imgpath))

    # Re-slice
    img = autoselect_time_frame(img)
    img = slice_k_d_img(img, 3)

    # Re-scale if deconvolved
    img = (img / get_rescaling_factor(imgpath, imgdir)).astype('float')

    # Pick first timeframe (also for 2D images)
    if 3 == len(img.shape) and 1 == img.shape[0]:
        img = img[0]

    # Binarize -----------------------------------------------------------------
    
    # Segment
    mask_global = binarize(img, threshold_otsu(img))
    mask_local = threshold_adaptive(img, neighbour_side)
    mask = np.logical_and(mask_global, mask_local)

    # Remove objects touch XY contour
    mask = clear_borders(mask, False)

    # Fill holes (3D)
    mask = ndi.binary_fill_holes(mask)
    if 3 == len(mask.shape):
        for sliceid in range(mask.shape[0]):
            slide = mask[sliceid, :, :]
            mask[sliceid, :, :] = ndi.binary_fill_holes(slide)

    # Filter based on object size
    mask = filter_obj_XY_size(mask, radius_interval)
    mask = filter_obj_Z_size(mask, min_z_size)

    # Identify nuclei
    L = label(mask)

    # Output -------------------------------------------------------------------
    outpath = "%s%s" % (outdir, outprefix + imgpath)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        io.imsave(outpath, L.astype('u4'))
    print("Segmentation output written to %s" % (outpath,))

    return(outpath)

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
    delayed(run_segmentation)(imgpath, imgdir)
    for imgpath in imglist)

# END ==========================================================================

################################################################################
