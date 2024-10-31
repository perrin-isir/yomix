import bokeh.models


def gene_query_button(offset_text_feature_color):
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
