Plotting
========

The plotting module sets up the plots, the legend and all the buttons and widgets 
to interact with the data.

More precisely, it is responsible for:

- Creating the main Bokeh figure and rendering the 2D or 3D data embedding from an
  AnnData object.

- Implementing the complex client-side JavaScript callbacks that enable
  real-time 3D rotation (yaw, pitch, roll) and depth perception.

- Setting up standard Bokeh tools like HoverTool, LassoSelectTool, and sliders
  for user interaction.

- Coloring data points on the main scatter plot based on the values of one or
  more user-selected features.

- Generating violin plots and heatmaps, to visualize the distribution of feature
  values across different user-defined subsets or existing categorical labels.

- Managing the data sources and handling updates based on user interactions.


.. automodule:: yomix.plotting.features
   :members:
   :undoc-members:
   :show-inheritance:


.. automodule:: yomix.plotting.figure
   :members:
   :undoc-members:
   :show-inheritance:


.. automodule:: yomix.plotting.legend
   :members:
   :undoc-members:
   :show-inheritance:
