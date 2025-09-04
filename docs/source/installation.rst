Getting started
===============

This section explains how to install and use the `yomix` tool.

Install via pip
---------------

In a Python virtual environment, do the following:

.. code:: bash

   pip install yomix

Try the tool with the example dataset:

.. code:: bash
   
   yomix --example


Install from Source
-------------------


.. code:: bash
   
   git clone https://github.com/perrin-isir/yomix.git

We recommend using `micromamba <https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html#>`__ to create a Python environment, but you can use any Python package manager instead.
   
   
.. code:: bash

   cd yomix

   micromamba create --name yomixenv --file environment.yaml

   micromamba activate yomixenv

   pip install -e .

Then try the tool with:

.. code:: bash

   yomix yomix/example/pbmc.h5ad

To use it on your own files:
----------------------------

.. code:: bash

   yomix yourfile.h5ad

where ``yourfile.h5ad`` is an AnnData object saved in `.h5ad` format (see `anndata - Annotated data <https://anndata.readthedocs.io/en/latest/index.html#>`__) with at least one `.obsm` field of dimension 2 or more.

Launch YOMIX from a jupyter notebook
------------------------------------

Run those commands in a cell of your notebook:
   
.. code-block:: python

   import anndata
   from yomix.server import start_server

   xd = anndata.read_h5ad("yomix/example/pbmc.h5ad")
   start_server(xd)

Improve reactiveness with subsampling
-------------------------------------

When there are many samples in the dataset, you can use the `--subsampling` option to improve reactiveness. This option will randomly subsample the dataset to a maximum number of `N` samples. For example:

.. code:: bash

   yomix --subsampling 5000 yourfile.h5ad

This will subsample the dataset to a maximum of 5000 samples.
