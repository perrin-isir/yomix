# ![alt text](https://raw.githubusercontent.com/perrin-isir/yomix/main/yomix/assets/yomix_logo.png "Yomix logo")

[![codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Yomix is an interactive tool to explore low dimensional embeddings of omics data.

## INSTALL

In a python virtual environment, do:

    pip install yomix


Then try the tool with:

    yomix --example


To use it on your own files:

    yomix yourfile.h5ad

where `yourfile.h5ad` is an anndata object saved in h5ad format (see
 [anndata - Annotated data](https://anndata.readthedocs.io/en/latest/index.html#)), 
 with at least one `.obsm` field of dimension 2 or more.

When there are many samples in the dataset, the --subsampling option can be passed to improve reactiveness:

    yomix --subsampling N yourfile.h5ad

It randomly subsamples the dataset to a maximum number of N samples. For example:

    yomix --subsampling 5000 yourfile.h5ad


<details><summary> <b>Other option: INSTALL FROM SOURCE</b> </summary><p>

    git clone https://github.com/perrin-isir/yomix.git


We recommand to create a python environment with [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html),
but any python package manager can be used instead.

    cd yomix

    micromamba create --name yomixenv --file environment.yaml

    micromamba activate yomixenv

    pip install -e .


Then try the tool with:

    yomix yomix/example/pbmc.h5ad

The input file must be an anndata object saved in h5ad format (see
 [anndata - Annotated data](https://anndata.readthedocs.io/en/latest/index.html#)), 
 with at least one `.obsm` field of dimension 2 or more.

</p></details>

## List of contributors

Nicolas Perrin-Gilbert

Joshua Waterfall

Pierre Fumeron

Nisma Amjad

Jason Z. Kim

Erkan Narmanli

Christopher R. Myers

James P. Sethna

Jérôme Contant

Thomas Fuks

Julien Vibert
