yomix.plotting.figure
=====================

This module provides tools for creating and customizing the main figure for data visualizations, including handling embeddings and plot sizing.

Functions
---------

.. py:function:: main_figure(adata, embedding_key, width=900, height=600, title='')
   :module: yomix.plotting.figure

   Creates the main figure for visualizing data, typically using embeddings from the provided AnnData object.

   :param adata: The AnnData object containing the data, including embeddings and other information.
   :type adata: AnnData

   :param embedding_key: The key in `adata.obsm` that contains the embedding (e.g., 'X_pca', 'X_umap').
   :type embedding_key: str

   :param width: The width of the figure in pixels (default is 900).
   :type width: int, optional

   :param height: The height of the figure in pixels (default is 600).
   :type height: int, optional

   :param title: The title of the figure (default is an empty string).
   :type title: str, optional

   :returns: A Bokeh `figure.Figure` object representing the main visualization.
   :rtype: Bokeh.plotting.figure.Figure

