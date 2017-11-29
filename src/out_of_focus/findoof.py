#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# 
# Author: Gabriele Girelli
# Email: gigi.ga90@gmail.com
# Version: 0.0.1
# Date: 20171129
# Project: bioimaginb
# Description: extract intensity distribution on Z.
# 
# ------------------------------------------------------------------------------



# DEPENDENCIES =================================================================

import argparse
import os
import re
import skimage.io as io

# PARAMETERS ===================================================================


# Add script description
parser = argparse.ArgumentParser(
    description = 'Extract intensity distribution on Z for every image.'
)

# Add mandatory arguments
parser.add_argument('imdir', type = str, nargs = 1,
    help = 'Path to folder with tiff images.')
parser.add_argument('output', type = str, nargs = 1,
    help = 'Path to output table file.')

# Add arguments with default value
parser.add_argument('--range', type = float, nargs = 1, metavar = 'range',
    help = '''Specify %% of stack where the maximum of intensity distribution
    over Z is expected for an in-focus field of view. Default: 50%%''',
    default = [.5])
parser.add_argument('--pattern', type = str, nargs = 1, metavar = 'regexp',
    help = '''Provide a regular expression pattern matching the images in the
    image folder that you want to check. Default: "^.*\.tif$"''',
    default = ["^.*\.tif$"])

# Parse arguments
args = parser.parse_args()

# Assign to in-script variables
imdir = args.imdir[0]
fout_path = args.output[0]
prange = args.range[0]
pattern = args.pattern[0]

# FUNCTIONS ====================================================================

# RUN ==========================================================================

# Add trailing slash to image folder path
if not "/" == imdir[-1]:
    imdir += "/"

# Check that image folder path exists
if not os.path.isdir(imdir):
    sys.exit("!ERROR: specified imdir does not exist.\n%s" % (imdir,))

# Open buffer to output file
fout = open(fout_path, "w+")

# Identify tiff images
flist = []
for (dirpath, dirnames, filenames) in os.walk(imdir):
    flist.extend(filenames)
    break
imlist = [f for f in flist if not type(None) == type(re.match(pattern, f))]

# Iterate through fields of view
for impath in imlist:
    # Read image
    im = io.imread(imdir + impath)
    
    # Select first time frame
    while 3 < len(im.shape):
        im = im[0]

    # Iterate through slices
    intlist = []
    for zi in range(im.shape[0]):
        # Save intensity sum
        intlist.append(im[zi].sum())

        # Write output table
        fout.write("%s\t%d\t%f\n" % (impath, zi + 1, intlist[zi]))


    # Identify maximum slice
    maxid = intlist.index(max(intlist))
    hrange = im.shape[0] * prange / 2.
    hstack = im.shape[0] / 2.
    if maxid >= (hstack - hrange) and maxid <= (hstack + hrange):
        print("%s is in-focus." % (impath,))
    else:
        print("%s is out-of-focus." % (impath,))

# Close buffer to output file
fout.close()

print("""
NOTE: use zplot.R to generate a PDF of the distributions. Simply run:
      ./zplot.R %s %s.pdf
""" % (fout_path, fout_path))

# END ==========================================================================

################################################################################
