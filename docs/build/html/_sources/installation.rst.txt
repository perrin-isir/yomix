Installation Guide
==================

This section explains how to install and use the `yomix` tool.

Install via pip
---------------

In a Python virtual environment, do the following:

1. Install `yomix` using pip:

   .. code:: bash

      pip install yomix

2. Try the tool with the example dataset:

   .. code:: bash

      yomix --example

To use it on your own files:
----------------------------

1. Ensure your input file is an AnnData object saved in `.h5ad` format (see `AnnData - Annotated Data <https://anndata.readthedocs.io/en/latest/>`) with at least one `.obsm` field of dimension 2 or more.
2. Run the following command:

   .. code:: bash

      yomix yourfile.h5ad

Where `yourfile.h5ad` is your own dataset in `.h5ad` format.

Improve Reactiveness with Subsampling
------------------------------------

When there are many samples in the dataset, you can use the `--subsampling` option to improve reactiveness. This option will randomly subsample the dataset to a maximum number of `N` samples. For example:

   .. code:: bash

      yomix --subsampling 5000 yourfile.h5ad

This will subsample the dataset to a maximum of 5000 samples.

Install from Source
-------------------

If you prefer to install `yomix` from source, follow these steps:

1. Clone the repository:

   .. code:: bash

      git clone https://github.com/perrin-isir/yomix.git

   We recommend using `micromamba` to create a Python environment, but you can use any Python package manager instead.

2. Navigate to the `yomix` directory:

   .. code:: bash

      cd yomix

3. Create the environment using `micromamba`:

   .. code:: bash

      micromamba create --name yomixenv --file environment.yaml

4. Activate the environment:

   .. code:: bash

      micromamba activate yomixenv

5. Install the package in editable mode:

   .. code:: bash

      pip install -e .

6. Try the tool with an example file:

   .. code:: bash

      yomix yomix/example/pbmc.h5ad

The input file must be an AnnData object saved in `.h5ad` format with at least one `.obsm` field of dimension 2 or more.

Notes
-----

- The input file must be an `.h5ad` file containing an AnnData object with at least one `.obsm` field of dimension 2 or more (e.g., PCA, UMAP embeddings).

