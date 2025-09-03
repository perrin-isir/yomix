Frequently Asked Questions
==========================

Here are the answers to some common questions about YOMIX.

How to create embeddings ?
--------------------------
TODO 

How to convert my rfile to anndata ?
------------------------------------
You can use Seurat objects by converting them to .h5ad format in R:

Load required libraries::

    library(rhdf5)
    library(dplyr)
    library(patchwork)
    library(SeuratDisk)
    library(Seurat)
    library(SeuratData)


Load the object::

    my_file <- readRDS("path.rds")


If it is a SingleCellExperiment object, convert to Seurat::

    if (inherits(my_file, "SingleCellExperiment")) {
        my_file <- as.Seurat(my_file)
    }


Save as H5Seurat::

    SaveH5Seurat(my_file, filename = "filename.h5seurat")


Convert to .h5ad::

    Convert("filename.h5seurat", dest = "h5ad", output.path = "/.h5ad")


