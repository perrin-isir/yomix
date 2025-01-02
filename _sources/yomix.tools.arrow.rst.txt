yomix.tools.arrow
=================

This module provides functions for arrow manipulation.

Functions
---------

.. py:function:: arrow_function(points_bokeh_plot, adata, embedding_key, bt_slider_roll, bt_slider_pitch, bt_slider_yaw, source_rotmatrix_etc, bt_toggle_anim, hidden_checkbox_A, div_signature_list, multiselect_signature, sign_nr, sl_component1, sl_component2, sl_component3, label_sign)
   :module: yomix.tools.arrow

   Updates the arrow plot visualization based on the input parameters.

   :param points_bokeh_plot: The Bokeh plot object for rendering arrows.
   :type points_bokeh_plot: Bokeh.plotting.figure

   :param adata: The AnnData object containing single-cell data.
   :type adata: AnnData

   :param embedding_key: Key to retrieve embeddings from the AnnData object.
   :type embedding_key: str

   :param bt_slider_roll, bt_slider_pitch, bt_slider_yaw: Slider object controlling the rotation values.
   :type bt_slider_roll: Bokeh.models.Slider


   :param source_rotmatrix_etc: Data source for rotation matrix and other parameters.
   :type source_rotmatrix_etc: Bokeh.models.ColumnDataSource

   :param bt_toggle_anim: Toggle button for enabling/disabling animations.
   :type bt_toggle_anim: Bokeh.models.Toggle

   :param hidden_checkbox_A: A checkbox group used to manage which data points are in subset A.
   :type hidden_checkbox_A: Bokeh.models.CheckboxGroup

   :param div_signature_list: Div element displaying the signature list.
   :type div_signature_list: Bokeh.models.Div

   :param multiselect_signature: Multiselect widget for selecting signatures.
   :type multiselect_signature: Bokeh.models.MultiSelect

   :param sign_nr: Number indicating the selected signature.
   :type sign_nr: int

   :param sl_component1: Slider for adjusting component 1 of the visualization.
   :type sl_component1: Bokeh.models.Slider

   :param sl_component2: Slider for adjusting component 2 of the visualization.
   :type sl_component2: Bokeh.models.Slider

   :param sl_component3: Slider for adjusting component 3 of the visualization.
   :type sl_component3: Bokeh.models.Slider

   :param label_sign: A multi-select widget for selecting labels.
   :type label_sign: bokeh.models.MultiSelect

   :returns: The button to trigger the computation of the oriented signature.A help button that provides a tooltip with instructions about using the arrow tool.
   :rtype: None


