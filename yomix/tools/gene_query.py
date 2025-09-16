# """
# Provides a utility to query external databases for selected features.

# This module contains a function to create a button that, when clicked,
# searches for the currently selected feature names on the HUGO Gene
# Nomenclature Committee (HGNC) website. This provides a quick way for
# users to get more information about features of interest directly from
# the interface.
# """

import bokeh.models


def gene_query_button(
    offset_text_feature_color: bokeh.models.TextInput,
) -> bokeh.models.Button:
    """

    Create a button to search for genes in the HGNC database.

    This function generates a Bokeh Button when clicked, extracts the feature
    names from the feature input text box, and for each feature, opens a
    new browser tab to the corresponding search results page on the
    HGNC website. It may include `+` and `-` operators, as well as Ensembl IDs.

    Args:
        offset_text_feature_color (bokeh.models.TextInput):
            Text input for entering feature names to color samples in the scatter plot.

    Returns:
        btn_open_link (:class:`bokeh.models.Button`) :
            Button that opens HGNC search pages for the features listed in `offset_text_feature_color`.
    """  # noqa: E501

    bt_open_link = bokeh.models.Button(
        label="← Search these features in HGNC", width=235, height=60
    )

    bt_open_link.js_on_click(
        bokeh.models.CustomJS(
            args=dict(otfc=offset_text_feature_color),
            code="""
            var query_string = otfc.value;
            const ensembl_re = RegExp(/ENS(G|T|P)0[0-9]+/g);
            var q_list = query_string.split('  -  ').join('  +  ').split('  +  '
                            ).filter(element => element);
            q_list = q_list.map(
                elt => [].concat(elt.match(ensembl_re)).filter(
                    elt => elt).concat(elt)).map(elt => elt[0]);
            for (let i=0; i<q_list.length; i++) {
                window.open(
                    "https://www.genenames.org/tools/search/#!/?query=" + q_list[i],
                    '_blank');
            }
        """,
        )
    )

    return bt_open_link
