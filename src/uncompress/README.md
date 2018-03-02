tiff-tools-gg : uncompress
===

Uncompress contains standalone tools to read compress tiff files and save them in uncompressed format. This step is usually necessary to make them compatible with visualization softwares like ImageJ or FIJI. Keep in mind, uncompressed files will be larger in size. The `uncompress_tiff.py` tool allows to automatically uncompress all tiff files in a folder.

### Installation

A number of Python packages is required to run the script. Some are default packages: `argparse`, `sys`; while others are usually not present in a default Python setup and need to be manually added: `tifffile`.

### License

The `tiff-tools-gg` project is published under an MIT License, copyright (c) 2017 Gabriele Girelli.
