yomix.tools.gene_query
======================

This module provides functions for querying genes and interacting with gene-related features in visualizations.

Functions
---------

.. py:function:: gene_query_button(offset_text_feature_color)
   :module: yomix.tools.gene_query

   The function gene_query_button creates a button that, when clicked, processes the input from the offset_text_feature_color widget, extracts Ensembl IDs, and opens new browser tabs with the corresponding search results from the HGNC website.

   :param offset_text_feature_color: This parameter is passed into the function and represents a widget containing the user input text. 
   :type offset_text_feature_color: dict

   :returns: Updates the gene query from the HGNC website.
   :rtype: bokeh.models.Button

