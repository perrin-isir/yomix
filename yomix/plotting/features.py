from scipy.stats import gaussian_kde
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar, InlineStyleSheet
from bokeh.transform import linear_cmap
from bokeh.palettes import Viridis256
import bokeh.models
import bokeh.palettes
import re
import numpy as np


def color_by_feature_value(
    points_bokeh_plot,
    violins_bokeh_plot,
    heat_map,
    adata,
    select_color_by,
    hidden_text_label_column,
    resize_width_input,
    hidden_legend_width,
    hidden_checkbox_A,
    hidden_checkbox_B,
    resize_w_input,
    resize_h_input,
    bt_slider_range,
):
    source = points_bokeh_plot.select(dict(name="scatterplot"))[0].data_source

    feature_dict = {}
    feat_min = np.min(adata.X, axis=0)
    feat_max = np.max(adata.X, axis=0)

    for i, featname in enumerate(adata.var_names):
        feature_dict[featname] = [i, feat_min[i], feat_max[i]]

    def color_modif(
        stringval, htlc, rwi, hlw, label_stringval, resize_w, resize_h, bt_slider_range
    ):
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

        if label_stringval:
            selected_labels = [
                lbl.strip() for lbl in label_stringval.split("//yomix//") if lbl.strip()
            ]
        else:
            selected_labels = None

        plot_var_features = []
        for elt in positive_matches + negative_matches:
            if elt in feature_dict:
                plot_var_features += [elt]

        if len(plot_var_features) > 0 and selected_labels is not None:
            plot_var(
                adata,
                points_bokeh_plot,
                violins_bokeh_plot,
                heat_map,
                resize_w,
                resize_h,
                hidden_checkbox_A,
                hidden_checkbox_B,
                features=plot_var_features,
                selected_labels=selected_labels,
            )

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
                    new_data_color = (
                        adata.X[source.data["index"][:], feature_dict[elt][0]] - vmin
                    ) / (vmax - vmin + 0.000001)
                elif len(positive_matches) == 0 and len(negative_matches) == 1:
                    elt = negative_matches[0]
                    vmax = -feature_dict[elt][1]
                    vmin = -feature_dict[elt][2]
                    new_data_color = (
                        -adata.X[source.data["index"][:], feature_dict[elt][0]] - vmin
                    ) / (vmax - vmin + 0.000001)
                else:
                    new_data_color = np.zeros(len(source.data["color"]))
                    for elt in positive_matches:
                        vmin = feature_dict[elt][1]
                        vmax = feature_dict[elt][2]
                        new_data_color += (
                            adata.X[source.data["index"][:], feature_dict[elt][0]]
                            - vmin
                        ) / (vmax - vmin + 0.000001)
                    for elt in negative_matches:
                        vmax = -feature_dict[elt][1]
                        vmin = -feature_dict[elt][2]
                        new_data_color += (
                            -adata.X[source.data["index"][:], feature_dict[elt][0]]
                            - vmin
                        ) / (vmax - vmin + 0.000001)
                    new_data_color = new_data_color / (new_data_color.max() + 0.000001)
                source.data["color_ref"] = new_data_color

                htlc.value = ""
                viridis_colors = list(bokeh.palettes.Viridis256)
                custom_color_mapper = bokeh.models.LinearColorMapper(
                    palette=viridis_colors, low=0.0, high=1.0
                )

                def simple_shrink(s_in, size):
                    true_size = max(size, 3)
                    if len(s_in) > true_size:
                        new_s = ""
                        l1 = true_size - 3
                        new_s += s_in[:l1]
                        new_s += "..."
                    else:
                        new_s = s_in
                    return new_s

                cbar = bokeh.models.ColorBar(
                    color_mapper=custom_color_mapper,
                    label_standoff=12,
                    width=47,
                    ticker=bokeh.models.FixedTicker(ticks=[]),
                    title=simple_shrink(stringval, 50),
                )
                if points_bokeh_plot.right:
                    decrement = float(points_bokeh_plot.right[0].name)
                    points_bokeh_plot.right.pop(0)
                else:
                    decrement = 0.0
                legend_len = len(points_bokeh_plot.right)
                points_bokeh_plot.right = [cbar] + points_bokeh_plot.right
                # label_font_size = cbar.major_label_text_font_size
                # label_font_size = int(label_font_size[:-2])
                legend_width = cbar.width + 34
                cbar.name = str(legend_width)
                if legend_len > 0:
                    legend_width_modif = legend_width + float(hlw.value) - decrement
                else:
                    legend_width_modif = legend_width
                rwi.value = str(
                    int(points_bokeh_plot.width - float(hlw.value) + legend_width_modif)
                )
                hlw.value = str(int(legend_width_modif))
                select_color_by.value = ""
                current_style = bt_slider_range.stylesheets[0].css
                pattern = r"\{margin: 32px 0px 0px -\d+px;\}"
                new_style = re.sub(
                    pattern,
                    "{margin: 32px 0px 0px -"
                    + str(int(legend_width_modif) - 34)
                    + "px;}",
                    current_style,
                )
                bt_slider_range.stylesheets = [InlineStyleSheet(css=new_style)]
                bt_slider_range.start = 0.0
                bt_slider_range.end = 1.0
                bt_slider_range.value = (0.0, 1.0)
                bt_slider_range.step = 0.01
                bt_slider_range.visible = True

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

    offset_label = bokeh.models.TextInput(
        value="",
        title="Selected Groups:",
        name=" _plot",
        width=650,
    )

    offset_text_feature_color.on_change(
        "value",
        lambda attr, old, new: color_modif(
            new,
            hidden_text_label_column,
            resize_width_input,
            hidden_legend_width,
            offset_label.value,  # Include the current label value
            resize_w_input,
            resize_h_input,
            bt_slider_range,
        ),
    )

    # Modify the callback for offset_label
    offset_label.on_change(
        "value",
        lambda attr, old, new_label: color_modif(
            offset_text_feature_color.value,
            hidden_text_label_column,
            resize_width_input,
            hidden_legend_width,
            new_label,  # Pass the new label value to color_modif
            resize_w_input,
            resize_h_input,
            bt_slider_range,
        ),
    )

    return offset_text_feature_color, offset_label


def plot_var(
    adata,
    points_bokeh_plot,
    violins_bokeh_plot,
    heat_map,
    resize_w,
    resize_h,
    hidden_checkbox_A,
    hidden_checkbox_B,
    features,
    selected_labels=None,  # This is where the selected labels will be passed
    equal_size=False,
):

    def get_kde(data, grid_points=100):
        kde = gaussian_kde(data)
        y = np.linspace(np.min(data), np.max(data), grid_points)
        x = kde(y)
        return x, y

    def plot_violin_from_feat(xd, feat, labels, mode="violin"):
        data_tmp = {"x": [], "y": [], "median_expr": [], "alpha": []}
        step = 0
        labels_nr = len(labels)
        for label in labels:
            if label == "[  Subset A  ]":
                data = xd[hidden_checkbox_A.active, feat].X.toarray().reshape(-1)
                if np.any(data):
                    median_expr = np.median(data)
            elif label == "[  Subset B  ]":
                data = xd[hidden_checkbox_B.active, feat].X.toarray().reshape(-1)
                if np.any(data):
                    median_expr = np.median(data)
            elif label == "[  Rest  ]":
                idx = np.arange(adata.n_obs)[
                    ~np.isin(np.arange(xd.n_obs), hidden_checkbox_A.active)
                ]
                data = xd[idx, feat].X.toarray().reshape(-1)
                if np.any(data):
                    median_expr = np.median(data)
            else:
                lblsplit = label.split(">>yomix>>")
                lbl = lblsplit[0]
                lbl_elt = lblsplit[1]
                data = xd[xd.obs[lbl] == lbl_elt, feat].X.toarray().reshape(-1)
                if np.any(data):
                    if xd.var["yomix_median_" + label][feat] < 0:
                        xd.var.loc[feat, "yomix_median_" + label] = np.median(data)
                    median_expr = xd.var["yomix_median_" + label][feat]
            if np.any(data) and (len(data) > 1 or mode != "violin"):
                if mode == "violin":
                    x, y = get_kde(data)
                else:  # heatmap
                    x, y = np.ones(100), np.linspace(0, 1, 100)
                # same width for every subset
                x = (2.5 - np.clip(0.01 * labels_nr, 0, 0.1)) * x / np.max(x)
                data_tmp["x"].append(np.concatenate([x, -x[::-1]]) + step)
                data_tmp["y"].append(np.concatenate([y, y[::-1]]))
                data_tmp["median_expr"].append(median_expr)
                data_tmp["alpha"].append(1.0)
            elif np.any(data) and len(data) == 1 and mode == "violin":
                bound = 2.5 - np.clip(0.01 * labels_nr, 0, 0.1)
                line = np.linspace(step - bound, step + bound, 100)
                data_tmp["x"].append(line)
                data_tmp["y"].append([median_expr for i in line])
                data_tmp["median_expr"].append(median_expr)
                data_tmp["alpha"].append(1.0)
            else:
                if mode == "violin":
                    # line = np.linspace(step - 1, step + 1, 100)
                    bound = 2.5 - np.clip(0.01 * labels_nr, 0, 0.1)
                    line = np.linspace(step - bound, step + bound, 100)
                    data_tmp["x"].append(line)
                    data_tmp["y"].append([0 for i in line])
                    data_tmp["median_expr"].append(0)
                    data_tmp["alpha"].append(1.0)
                else:
                    x, y = np.ones(100), np.linspace(0, 1, 100)
                    x = (2.5 - np.clip(0.01 * labels_nr, 0, 0.1)) * x / np.max(x)
                    data_tmp["x"].append(np.concatenate([x, -x[::-1]]) + step)
                    data_tmp["y"].append(np.concatenate([y, y[::-1]]))
                    data_tmp["median_expr"].append(0)
                    data_tmp["alpha"].append(1.0)
            step += 5
        bound = 2.5 - np.clip(0.01 * labels_nr, 0, 0.1)
        data_tmp["x"].append(np.linspace(0 - bound, step - 5 + bound, 100))
        data_tmp["y"].append(np.ones(100))
        data_tmp["median_expr"].append(0)
        data_tmp["alpha"].append(0.2)
        data_tmp["x"].append(np.linspace(0 - bound, step - 5 + bound, 100))
        data_tmp["y"].append(0.0 * np.ones(100))
        data_tmp["median_expr"].append(0)
        data_tmp["alpha"].append(0.2)
        return data_tmp

    def refresh_violin(vplot, mode="violin"):
        data_tmp = {"x": [], "y": [], "median_expr": [], "alpha": []}

        step_yaxis = 0
        if selected_labels is None:
            labels = None
        else:
            labels = selected_labels

        for feat in features[::-1]:
            tmp_dict = plot_violin_from_feat(adata, feat, labels, mode=mode)
            tmp_dict["y"] = [np.asarray(i) + step_yaxis for i in tmp_dict["y"]]
            for key in data_tmp.keys():
                data_tmp[key].extend(tmp_dict[key])
            step_yaxis += 1.1

        vplot.yaxis.major_label_text_font_size = "10pt"
        if len(features) > 1:
            set_yticks = [0.5 + 1.1 * i for i in range(len(features))]
            vplot.yaxis.ticker = set_yticks
            vplot.yaxis.major_label_overrides = {
                set_yticks[i]: features[len(features) - i - 1]
                for i in range(len(features))
            }
            vplot.yaxis.axis_label = ""
        else:
            vplot.yaxis.axis_label = features[0]
            set_yticks = []
            vplot.yaxis.ticker = set_yticks
            vplot.yaxis.major_label_overrides = {}

        custom_color_mapper = LinearColorMapper(palette=Viridis256, low=0, high=1)

        # check if patches already exist
        if vplot.select(name="violins"):
            source = vplot.select(dict(name="violins"))[0].data_source
            source.data = data_tmp
        else:
            source = ColumnDataSource(data=data_tmp)
            vplot.patches(
                "x",
                "y",
                source=source,
                fill_color=linear_cmap(
                    "median_expr", palette=Viridis256, low=0, high=1
                ),
                line_alpha="alpha",
                line_color="black",
                name="violins",
            )
            color_bar = ColorBar(
                color_mapper=custom_color_mapper,
                title="Normalized median feature value in group",
                title_text_align="center",
                major_tick_line_color=None,
                major_label_text_font_size="0pt",
            )
            vplot.add_layout(color_bar, "right")

        vplot.title.text = "Feature values per group"
        vplot.xgrid.visible = False
        vplot.ygrid.visible = False

        set_xticks = list(range(0, len(labels) * 5, 5))
        vplot.xaxis.ticker = set_xticks
        samples_per_labels = {}
        text_labels = []
        for label in labels:
            if label == "[  Subset A  ]":
                samples_per_labels["[  Subset A  ]"] = str(
                    len(hidden_checkbox_A.active)
                )
                text_labels.append(label + "\n ")
            elif label == "[  Subset B  ]":
                samples_per_labels["[  Subset B  ]"] = str(
                    len(hidden_checkbox_B.active)
                )
                text_labels.append(label + "\n ")
            elif label == "[  Rest  ]":
                samples_per_labels["[  Rest  ]"] = str(
                    len(adata) - len(hidden_checkbox_A.active)
                )
                text_labels.append(label + "\n ")
            else:
                lblsplit = label.split(">>yomix>>")
                lbl = lblsplit[0]
                lbl_elt = lblsplit[1]
                samples_per_labels[label] = str(len(adata[adata.obs[lbl] == lbl_elt]))
                text_labels.append(lbl + "\n" + lbl_elt)

        vplot.xaxis.major_label_overrides = {
            set_xticks[i]: (
                text_labels[i] + "\n\n" + samples_per_labels[labels[i]] + "\nsamples"
                if int(samples_per_labels[labels[i]]) > 1
                else text_labels[i]
                + "\n\n"
                + samples_per_labels[labels[i]]
                + "\nsample"
            )
            for i in range(len(set_xticks))
        }

        vplot.visible = True

    refresh_violin(violins_bokeh_plot, mode="violin")
    refresh_violin(heat_map, mode="heatmap")

    resize_w.visible = True
    resize_h.visible = True
