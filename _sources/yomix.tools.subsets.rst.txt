yomix.tools.subsets
===================

This module provides tools for creating and managing interactive buttons for selecting and modifying subsets of data in visualizations.

Functions
---------

.. py:function:: subset_buttons(points_bokeh_plot, source_rotmatrix_etc)
   :module: yomix.tools.subsets

   The subset_buttons function creates a set of interactive controls for selecting and highlighting subsets A and B in a scatter plot. By toggling these subsets on and off, and selecting subsets with buttons, the plot updates in real-time, adjusting the point sizes, colors, and other visual properties accordingly

   :param points_bokeh_plot: A Bokeh plot object that contains the scatter plot to be interacted with. This plot has a data source, which stores the data points.
   :type points_bokeh_plot: Bokeh.plotting.figure

   :param source_rotmatrix_etc: An object containing additional data that is used for modifying the point sizes (size_coef), possibly for scaling based on interactions.
   :type source_rotmatrix_etc: Bokeh.models.ColumnDataSource

   :returns: Updates the plot with the selected subset and modifies the data source accordingly.
   :rtype: tupple

