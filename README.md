> **Disclaimer: this repo has been archived and moved to [pygpseq](http://github.com/ggirelli/pygpseq)!  
> Check the [pre-merge](https://github.com/ggirelli/tiff-tools-gg/tree/pre-merge) branch for the pre-merge code.**

## How to switch to the pre-merge version (branch not maintained anymore)

From within the repository folder run the following:

```
git fetch
git checkout pre-merge
```

I would strongly advise to uninstall `tiff-tools-gg` and switch to `pygpseq` instead:

```
rm -rf tiff-tools-gg
git clone http://github.com/ggirelli/gpseq-seq-py
cd gpseq-seq-py
sudo -H pip3 install -e .
```
