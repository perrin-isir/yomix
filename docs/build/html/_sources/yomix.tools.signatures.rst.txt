yomix.tools.signatures
=======================

This module provides tools for managing and interacting with gene signatures in visualizations.

Functions
---------

.. py:function:: signature_buttons(adata, offset_text_feature_color, offset_label, hidden_checkbox_A, hidden_checkbox_B)
   :module: yomix.tools.signatures

   Designed to create and manage an interactive visualization tool for computing and displaying "signatures" based on the statistical differences between two or more subsets of a dataset. here we calaculate the signature subset A vs subset B or subset A vs rest. It gives us 20 sigantures. 

   :param adata: The AnnData object containing single-cell data.
   :type adata: AnnData

   :param offset_text_feature_color: Offset for text feature colors in the visualization.
   :type offset_text_feature_color: bokeh.models.Div

   :param offset_label: Offset for label positioning in the visualization.
   :type offset_label: bokeh.models.Div

   :param hidden_checkbox_A: A Bokeh checkbox group widget that tracks which cells belong to "Subset A"
   :type hidden_checkbox_A: Bokeh.models.widgets.CheckboxGroup

   :param hidden_checkbox_B: A Bokeh checkbox group widget that tracks which cells belong to "Subset B". 
   :type hidden_checkbox_B: Bokeh.models.widgets.CheckboxGroup

   :returns: A tuple containing 8 elements: Bokeh model objects and a list (for tracking the signature number).
   :rtype: The function returns a tuple of the above Bokeh. 

