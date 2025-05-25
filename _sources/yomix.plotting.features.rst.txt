yomix.plotting.features
=======================

This module provides tools for visualizing features in various formats such as scatter plots, violin plots, heatmaps, and more. It includes functionality for customizing plot colors and resizing, as well as managing data visualization features.

Functions
---------

.. py:function:: color_by_feature_value(points_bokeh_plot, violins_bokeh_plot, heat_map, adata, select_color_by, hidden_text_label_column, resize_width_input, hidden_legend_width, hidden_checkbox_A, hidden_checkbox_B, resize_w_input, resize_h_input)
   :module: yomix.plotting.features

   This function allows the user to color data points on a scatter plot (Bokeh plot) based on the value of a feature from the input data (adata). It provides interactivity for selecting features, which are then used to modify the color of the scatter plot points.

   :param points_bokeh_plot: The Bokeh scatter plot object that displays the points.
   :type points_bokeh_plot: Bokeh.plotting.figure.Figure

   :param violins_bokeh_plot: The Bokeh violin plot object for visualizing distributions.
   :type violins_bokeh_plot: Bokeh.plotting.figure.Figure

   :param heat_map: The heatmap object that displays a heatmap of feature values.
   :type heat_map: Bokeh.plotting.figure.Figure

   :param adata: The AnnData object containing the single-cell data, which includes the features to color by.
   :type adata: AnnData

   :param select_color_by: A dropdown or text input widget for selecting the feature to color by.
   :type select_color_by: str

   :param hidden_text_label_column: The column to use for labeling the points with text labels.
   :type hidden_text_label_column: str

   :param resize_width_input: The input width for resizing the plot's elements.
   :type resize_width_input: int

   :param hidden_legend_width: The width of the legend in the visualization.
   :type hidden_legend_width: int

   :param hidden_checkbox_A: A hidden checkbox controlling specific plot options or features.
   :type hidden_checkbox_A: Bokeh.models.widgets.CheckboxGroup

   :param hidden_checkbox_B: Another hidden checkbox for additional plot control.
   :type hidden_checkbox_B: Bokeh.models.widgets.CheckboxGroup

   :param resize_w_input: Width of the resized plot.
   :type resize_w_input: int

   :param resize_h_input: Height of the resized plot.
   :type resize_h_input: int

   :returns: Allows the user to input a feature name to color the scatter plot. Allows the user to input labels or groups, affecting how data is visualized in the violin and heatmap plots.
   :rtype: tuple of textinput 

.. py:function:: plot_var(adata, points_bokeh_plot, violins_bokeh_plot, heat_map, resize_w, resize_h, hidden_checkbox_A, hidden_checkbox_B, features, selected_labels=None, equal_size=False)
   :module: yomix.plotting.features

   This function generates a violin plot and heatmap for the feature values across different subsets of data. It computes kernel density estimates (KDEs) for the data and visualizes distributions for different labels in the dataset.

   :param adata: The AnnData object containing the data to be visualized.
   :type adata: AnnData

   :param points_bokeh_plot: The Bokeh scatter plot for displaying the data points.
   :type points_bokeh_plot: Bokeh.plotting.figure.Figure

   :param violins_bokeh_plot: The Bokeh violin plot for visualizing feature distributions.
   :type violins_bokeh_plot: Bokeh.plotting.figure.Figure

   :param heat_map: The heatmap showing feature values for cells or conditions.
   :type heat_map: Bokeh.plotting.figure.Figure

   :param resize_w: The width for resizing the plot.
   :type resize_w: int

   :param resize_h: The height for resizing the plot.
   :type resize_h: int

   :param hidden_checkbox_A: A hidden checkbox for controlling plot-specific options.
   :type hidden_checkbox_A: Bokeh.models.widgets.CheckboxGroup

   :param hidden_checkbox_B: A hidden checkbox for controlling additional options.
   :type hidden_checkbox_B: Bokeh.models.widgets.CheckboxGroup

   :param features: The list of features (columns from the AnnData object) to be plotted.
   :type features: list

   :param selected_labels: The labels to be selected for plotting, optional.
   :type selected_labels: list, optional

   :param equal_size: Whether to enforce equal sizing for the plots, optional.
   :type equal_size: bool, optional

   :returns: he function modifies the violins_bokeh_plot and heat_map objects in place, but it does not return any value.
   :rtype: None

