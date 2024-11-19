yomix.plotting.legend
=====================

This module provides tools for creating interactive buttons that allow users to select and manipulate subsets of data in visualizations.

Functions
---------

.. py:function:: setup_legend (pb_plot, obs_string, obs_numerical, source_rotmatrix_etc, resize_width_input)
   :module: yomix.plotting.legend

   Creates a complex utility designed for a Bokeh plot that allows dynamic creation and manipulation of a legend based on selected attributes (columns) from the plot's data.

   :param pb_plot: This is the main Bokeh plot object to which various interactive components, such as legends, text inputs, and color mappings, will be added.
   :type points_bokeh_plot: Bokeh.plotting.figure.Figure

   :param obs_string: A list of strings representing categorical (string) variables in the dataset that will be used for creating color categories or grouping.
   :type source_rotmatrix_etc: str
   
   :param obs_numerical:  A list of strings representing numerical (float or int) variables in the dataset that can be used for color mapping based on continuous values.
   :type source_rotmatrix_etc: str
   
   :param source_rotmatrix_etc:   It appears to be used for managing the width of the legend and updating this value dynamically.
   :type source_rotmatrix_etc: Bokeh.Columnsource
   
   :param resize_width_input: Represents the width of the plot, likely related to resizing behavior.
   :type source_rotmatrix_etc: int
   
   :returns: The function returns a tuple containing three Bokeh widgets.
   :rtype: tuple
