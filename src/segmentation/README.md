tiff-tools-gg : segmentation
===

Segmentation contains standalone tools to perform segmentation of tiff images. The `auto3Dsegment.py` tool allows to automatically segment nuclear staining images, preferably after deconvolving them.

### Installation

A number of Python packages is required to run the script. Some are default packages: `argparse`, `math`, `os`, `re`, `sys`, `warnings`; while others are usually not present in a default Python setup and need to be manually added: `joblib`, `multiprocessing`, `numpy`, `scipy`, `skimage`.

### Usage

```
usage: auto3Dsegment.py [-h] [--inreg INREG] [--outprefix OUTPREFIX]
                        [--neighbour NEIGHBOUR] [--radius RADIUS RADIUS]
                        [--minZ MINZ] [--threads THREADS] [--version]
                        imgFolder outFolder

Perform automatic 3D segmentation of DNA staining. Images are first identified
based on a regular expression matching the file name. Then, they are first re-
scaled if deconvolved with Huygens software, then a global (Otsu) and local
(median) thresholds are combined to binarize the image in 3D. Then, holes are
filled in 3D and a closing operation is performed to remove small objects.
Objects are filtered based on volume and Z size, and those touching the XY
contour of the image are discarded. The generated images have identified
objects labeled with different intensity levels.

positional arguments:
  imgFolder             Path to folder containing deconvolved tiff images.
  outFolder             Path to output folder where binarized images will be
                        stored (created if does not exist).

optional arguments:
  -h, --help            show this help message and exit
  --inreg INREG         regular expression to identify images from imgFolder.
                        Default: '^.*\.tiff?$'
  --outprefix OUTPREFIX
                        prefix to add to the name of output binarized images.
                        Default: 'mask_'
  --neighbour NEIGHBOUR
                        Side of neighbourhood square/cube. Default: 101
  --radius RADIUS RADIUS
                        Range of object radii [vx] to be considered a nucleus.
                        Default: [10, Inf]
  --minZ MINZ           Minimum fraction of stack occupied by an object to be
                        considered a nucleus. Default: .25
  --threads THREADS     number of threads for parallelization. Default: 1
  --version             show program's version number and exit
```

### License

The `tiff-tools-gg` project is published under an MIT License, copyright (c) 2017 Gabriele Girelli.
