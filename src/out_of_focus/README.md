tiff-tools-gg : out-of-focus
===

Based on the observation that, in case of in-focus field of views, cells should be laying in the central area of the Z-stack, I implemented `findoof.py`.

`findoof.py` takes as input the path to a folder with `.tif` image. The user can also specify a regular expression to match the images in the specified folder, and the size of the central area used to identify in-focus images.

**NOTE: `findoof.py` should be run <u>only</u> on DNA staining images.**

```
usage: findoof.py [-h] [--range range] [--pattern regexp] imdir output

Extract intensity distribution on Z for every image.

positional arguments:
  imdir             Path to folder with tiff images.
  output            Path to output table file.

optional arguments:
  -h, --help        show this help message and exit
  --range range     Specify % of stack where the maximum of intensity
                    distribution over Z is expected for an in-focus field of
                    view. Default: 50%
  --pattern regexp  Provide a regular expression pattern matching the images
                    in the image folder that you want to check. Default:
                    "^.*\.tif$"
```

For each image, it calculates the integral of intensity over each slice, and generates as output a table with three columns:

- Image path.
- Slice index (i.e., Z coordinate).
- Integral fo sum intensity.

Also, the script specifies which images are in-focus and which are not, for example:

```
dapi_009_cmle.tif is out-of-focus.
dapi_002_cmle.tif is in-focus.
dapi_022_cmle.tif is out-of-focus.
```

At the end, `findoof.py` provides the command to run `zplot.R` to plot the distributions:

```
NOTE: use zplot.R to generate a PDF of the distributions. Simply run:
      ./zplot.R iJC793.tsv iJC793.tsv.pdf
```

## Requirements

Python packages:

- `argparse`
- `os`
- `re`
- `skimage`

R libraries:

- `argparser`
- `ggplot2`

