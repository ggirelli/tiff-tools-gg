tiff-tools-gg : uncompress
===

Uncompress contains standalone tools to read compress tiff files and save them in uncompressed format. This step is usually necessary to make them compatible with visualization softwares like ImageJ or FIJI. Keep in mind, uncompressed files will be larger in size. The `uncompress_tiff.py` tool allows to automatically uncompress all tiff files in a folder.

### Installation

A number of Python packages is required to run the script. Some are default packages: `argparse`, `sys`; while others are usually not present in a default Python setup and need to be manually added: `tifffile`.

### Usage

```
usage: uncompress_tiff.py [-h] [--inreg INREG] [--threads THREADS] [--version]
                          imgFolder outFolder

Uncompress all tiff files matching the specified pattern.

positional arguments:
  imgFolder          Path to folder containing deconvolved tiff images.
  outFolder          Path to output folder where binarized images will be
                     stored (created if does not exist).

optional arguments:
  -h, --help         show this help message and exit
  --inreg INREG      regular expression to identify images from imgFolder.
                     Default: '^.*\.tiff?$'
  --threads THREADS  number of threads for parallelization. Default: 1
  --version          show program's version number and exit
```

### License

The `tiff-tools-gg` project is published under an MIT License, copyright (c) 2017 Gabriele Girelli.
