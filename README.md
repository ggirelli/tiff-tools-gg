tiff-tools-gg (not maintained)
===

**Note! As of 2018-03-15 `tiff-tools-gg` was merged with [`gpseq-img-py`](http://github.com/ggirelli/gpseq-img-py) and is not maintained anymore.**

A few scripts to manage tiff images, more details on the format are available [here](http://www.fileformat.info/format/tiff/egff.htm).

Cheers!

└[∵┌]└[ ∵ ]┘[┐∵]┘

### `tiff_split.m`

`tiff_split.m` can be run on MATLAB as `tiff_split(filename, outfolder, small_side)`, and it splits the `filename` tiff image in smaller square tiff images of side `small_side` saving them in the `outfolder` folder. Use `help tiff_split` or `doc tiff_split` for more details.

### Conversion

Conversion tools are available in the [conversion](src/conversion/) sub folder.

### `out_of_focus`

Tools to identify out-of-focus fields of view from nuclear staining images are available in the [out_of_focus](src/out_of_focus/) sub folder.

### Segmentation

Segmentation tools are available in the [segmentation](src/segmentation/) sub folder.