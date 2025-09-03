YOMIX
=====
Yomix is an interactive tool to explore low dimensional embeddings of omics data.

As illustrated in the GIF below, users can explore embeddings—typically generated using dimensionality reduction techniques such as UMAP,
t-SNE, TriMap, or VAEs. Within these visualizations, users can identify clusters of interest and use a lasso tool to define specific subsets. 
Yomix can then compute gene signatures for these subsets almost instantaneously. For instance, it can identify gene signatures that best distinguish
subset A from the rest of the data, differentiate subset A from subset B, or find genes whose expression levels are most strongly correlated with a 
user-defined direction within subset A.

.. image:: https://raw.githubusercontent.com/perrin-isir/yomix/main/yomix/assets/yomix_gif.gif

Content
-------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   signatures
   faq

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   yomix.server
   yomix.plotting
   yomix.tools


