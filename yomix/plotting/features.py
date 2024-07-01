import bokeh.models
import bokeh.palettes
import re
import numpy as np


def color_by_feature_value(
    points_bokeh_plot,
    adata,
    select_color_by,
    hidden_text_label_column,
    resize_width_input,
    hidden_legend_width,
):
    source = points_bokeh_plot.select(dict(name="scatterplot"))[0].data_source

    feature_dict = {}
    feat_min = np.min(adata.X, axis=0)
    feat_max = np.max(adata.X, axis=0)

    for i, featname in enumerate(adata.var_names):
        feature_dict[featname] = [i, feat_min[i], feat_max[i]]

    def color_modif(stringval, htlc, rwi, hlw):
        stringval_modif = ("  +  " + stringval).replace("  +    -  ", "  -  ").replace(
            "  +    +  ", "  +  "
        ).replace("  +  ", "§§§§§§§§§§  +  ").replace(
            "  -  ", "§§§§§§§§§§  -  "
        ) + "§§§§§§§§§§"
        positive_matches = [
            elt[5:-10] for elt in re.findall("  \\+  .*?§§§§§§§§§§", stringval_modif)
        ]
        negative_matches = [
            elt[5:-10] for elt in re.findall("  \\-  .*?§§§§§§§§§§", stringval_modif)
        ]
        if len(positive_matches) + len(negative_matches) > 0:
            contn = True
            for elt in positive_matches + negative_matches:
                if elt not in feature_dict:
                    contn = False
            if contn:
                if len(positive_matches) == 1 and len(negative_matches) == 0:
                    elt = positive_matches[0]
                    vmin = feature_dict[elt][1]
                    vmax = feature_dict[elt][2]
                    new_data_color = np.empty(len(source.data["color"]))
                    for i in range(len(source.data["color"])):
                        new_data_color[i] = (
                            adata.X[source.data["index"][i], feature_dict[elt][0]]
                            - vmin
                        ) / (vmax - vmin + 0.000001)
                elif len(positive_matches) == 0 and len(negative_matches) == 1:
                    elt = negative_matches[0]
                    vmax = -feature_dict[elt][1]
                    vmin = -feature_dict[elt][2]
                    new_data_color = np.empty(len(source.data["color"]))
                    for i in range(len(source.data["color"])):
                        new_data_color[i] = (
                            -adata.X[source.data["index"][i], feature_dict[elt][0]]
                            - vmin
                        ) / (vmax - vmin + 0.000001)
                else:
                    new_data_color = np.empty(len(source.data["color"]))
                    for i in range(len(source.data["color"])):
                        new_data_color[i] = 0.0
                        for elt in positive_matches:
                            vmin = feature_dict[elt][1]
                            vmax = feature_dict[elt][2]
                            new_data_color[i] += (
                                adata.X[source.data["index"][i], feature_dict[elt][0]]
                                - vmin
                            ) / (vmax - vmin + 0.000001)
                        for elt in negative_matches:
                            vmax = -feature_dict[elt][1]
                            vmin = -feature_dict[elt][2]
                            new_data_color[i] += (
                                -adata.X[source.data["index"][i], feature_dict[elt][0]]
                                - vmin
                            ) / (vmax - vmin + 0.000001)
                    new_data_color = new_data_color / (new_data_color.max() + 0.000001)
                source.data["color_ref"] = new_data_color

                points_bokeh_plot.right = []
                htlc.value = ""
                viridis_colors = list(bokeh.palettes.Viridis256)
                custom_color_mapper = bokeh.models.LinearColorMapper(
                    palette=viridis_colors, low=0.0, high=1.0
                )
                cbar = bokeh.models.ColorBar(
                    color_mapper=custom_color_mapper,
                    label_standoff=12,
                    ticker=bokeh.models.FixedTicker(ticks=[]),
                )
                points_bokeh_plot.add_layout(cbar, "right")
                label_font_size = cbar.major_label_text_font_size
                label_font_size = int(label_font_size[:-2])
                legend_width = 33
                rwi.value = str(
                    int(points_bokeh_plot.width - float(hlw.value) + legend_width)
                )
                hlw.value = str(int(legend_width))
                select_color_by.value = ""

    source.js_on_change(
        "data",
        bokeh.models.CustomJS(
            args=dict(source=source),
            code="""
        const data = source.data;
        for (let i = 0; i < data["color"].length; i++) {
            data["color"][i] = data["color_ref"][data["index"][i]];
        }
    """,
        ),
    )

    offset_text_feature_color = bokeh.models.TextInput(
        value="",
        title="Color by feature value (enter feature name):",
        name="offset_text_feature_color",
        width=650,
    )

    offset_text_feature_color.on_change(
        "value",
        lambda attr, old, new: color_modif(
            new, hidden_text_label_column, resize_width_input, hidden_legend_width
        ),
    )

    return offset_text_feature_color
