YOMIX
=====
Yomix is an interactive tool to explore low dimensional embeddings of omics data.
It is data agnostic : it can be used on Bulk and single-cell RNA-seq, DNA methylation data etc...

.. image:: https://raw.githubusercontent.com/perrin-isir/yomix/main/yomix/assets/yomix_gif.gif

As illustrated in the GIF above, users can explore embeddings—typically generated using dimensionality reduction techniques such as *UMAP*,
*t-SNE*, *TriMap*, or *VAEs*. Within these visualizations, users can identify clusters of interest and use a lasso tool to define specific subsets. 
Yomix can then compute feature signatures for these subsets almost instantaneously. 
It can identify feature signatures that best distinguish subset A from the rest of the data, 
differentiate subset A from subset B, or find features whose expression levels are most strongly correlated with a 
user-defined direction within subset A.



Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   tutorial
   signatures
   faq

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   yomix.server
   yomix.plotting
   yomix.tools


