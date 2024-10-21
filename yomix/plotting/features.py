from scipy.stats import gaussian_kde
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar
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
):
    source = points_bokeh_plot.select(dict(name="scatterplot"))[0].data_source

    feature_dict = {}
    feat_min = np.min(adata.X, axis=0)
    feat_max = np.max(adata.X, axis=0)

    for i, featname in enumerate(adata.var_names):
        feature_dict[featname] = [i, feat_min[i], feat_max[i]]

    def color_modif(stringval, htlc, rwi, hlw, label_stringval):
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
                lbl.strip() for lbl in label_stringval.split(",") if lbl.strip()
            ]
        else:
            selected_labels = None
        
        plot_var_features = []
        for elt in positive_matches + negative_matches:
            if elt in feature_dict:
                plot_var_features += [elt]

        print(positive_matches)
        print(plot_var_features)
        if len(plot_var_features) > 0:
            plot_var(
                adata,
                points_bokeh_plot,
                violins_bokeh_plot,
                heat_map,
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
        ),
    )

    return offset_text_feature_color, offset_label


def plot_var(
    adata,
    points_bokeh_plot,
    violins_bokeh_plot,
    heat_map,
    hidden_checkbox_A,
    hidden_checkbox_B,
    features,
    selected_labels=None,  # This is where the selected labels will be passed
    equal_size=False,
):

    def var_indices(adata) -> dict:
        vi_dict = {}
        for i, s_id in enumerate(adata.var_names):
            vi_dict[s_id] = i
        return vi_dict


    def obs_indices(adata) -> dict:
        oi_dict = {}
        for i, s_id in enumerate(adata.obs_names):
            oi_dict[s_id] = i
        return oi_dict


    def all_labels(labels) -> np.ndarray:
        return np.array(list(dict.fromkeys(labels)))


    def indices_per_label(labels) -> dict:
        i_per_label = {}
        for i, annot in enumerate(labels):
            i_per_label.setdefault(annot, [])
            i_per_label[annot].append(i)
        return i_per_label

    adata.uns["all_labels"] = all_labels(adata.obs["label"])
    adata.uns["obs_indices_per_label"] = indices_per_label(adata.obs["label"])
    adata.uns["var_indices"] = var_indices(adata)

    def get_kde(data, grid_points=100):
        kde = gaussian_kde(data)
        y = np.linspace(np.min(data), np.max(data), grid_points)
        x = kde(y)
        return x, y

    def plot_violin_from_gene(xd, gene, labels):
        min_norm = np.min(xd[:, gene].X.toarray())
        max_norm = np.max(xd[:, gene].X.toarray())
        data_tmp = {"x": [], "y": [], "median_gene_expr": []}
        step = 0
        labels_nr = len(labels)
        for label in labels:
            if label == "[  Subset A  ]":
                data = xd[hidden_checkbox_A.active, gene].X.toarray().reshape(-1)
            elif label == "[  Subset B  ]":
                data = xd[hidden_checkbox_B.active, gene].X.toarray().reshape(-1)
            elif label == "[  Rest  ]":
                idx = np.arange(adata.n_obs)[
                    ~np.isin(np.arange(xd.n_obs), hidden_checkbox_A.active)
                ]
                data = xd[idx, gene].X.toarray().reshape(-1)
            else:
                data = xd[xd.obs["label"] == label, gene].X.toarray().reshape(-1)
            if np.any(data):
                data_normalized = np.divide(data - min_norm, max_norm - min_norm)
                x, y = get_kde(data_normalized)
                # print(len(x), len(y))
                x, y = np.ones(100), np.linspace(0,1,100)
                # same width for every subset
                x = (2.5 - np.clip(0.01 * labels_nr, 0, 0.1)) * x / np.max(x)
                data_tmp["x"].append(np.concatenate([x, -x[::-1]]) + step)
                data_tmp["y"].append(np.concatenate([y, y[::-1]]))
                data_tmp["median_gene_expr"].append(np.median(data_normalized))
            else:
                # line = np.linspace(step - 1, step + 1, 100)
                bound = 2.5 - np.clip(0.01 * labels_nr, 0, 0.1)
                line = np.linspace(step - bound, step + bound, 100)
                data_tmp["x"].append(line)
                data_tmp["y"].append([0 for i in line])
                data_tmp["median_gene_expr"].append(0)
            step += 5
        return data_tmp

    data_tmp = {"x": [], "y": [], "median_gene_expr": []}

    step_yaxis = 0
    if selected_labels is None:
        labels = None
    else:
        labels = selected_labels

    for gene in features:
        tmp_dict = plot_violin_from_gene(adata, gene, labels)
        tmp_dict["y"] = [np.asarray(i) + step_yaxis for i in tmp_dict["y"]]
        for key in data_tmp.keys():
            data_tmp[key].extend(tmp_dict[key])
        step_yaxis += 1.1

    if len(features) > 1:
        set_yticks = [0.5 + 1.1 * i for i in range(len(features))]
        violins_bokeh_plot.yaxis.ticker = set_yticks
        violins_bokeh_plot.yaxis.major_label_overrides = {
            set_yticks[i]: features[i] for i in range(len(features))
        }
        violins_bokeh_plot.yaxis.axis_label = ""
        violins_bokeh_plot.yaxis.major_label_text_font_size = "10pt"
    else:
        violins_bokeh_plot.yaxis.axis_label = features[0]
        violins_bokeh_plot.yaxis.major_tick_line_color = None
        violins_bokeh_plot.yaxis.minor_tick_line_color = None
        violins_bokeh_plot.yaxis.major_label_text_font_size = "0pt"

    custom_color_mapper = LinearColorMapper(palette=Viridis256, low=0, high=1)

    # check if patches already exist
    if violins_bokeh_plot.select(name="violins"):
        source = violins_bokeh_plot.select(dict(name="violins"))[0].data_source
        source.data = data_tmp
    else:
        source = ColumnDataSource(data=data_tmp)
        violins_bokeh_plot.patches(
            "x",
            "y",
            source=source,
            fill_color=linear_cmap(
                "median_gene_expr", palette=Viridis256, low=0, high=1
            ),
            line_color="black",
            name="violins",
        )
        color_bar = ColorBar(
            color_mapper=custom_color_mapper,
            title="Median feature value in group",
            title_text_align="center",
            major_tick_line_color=None,
            major_label_text_font_size="0pt",
        )
        violins_bokeh_plot.add_layout(color_bar, "right")

    violins_bokeh_plot.title.text = "Feature values per group"
    violins_bokeh_plot.xgrid.visible = False
    violins_bokeh_plot.ygrid.visible = False

    set_xticks = list(range(0, len(labels) * 5, 5))
    violins_bokeh_plot.xaxis.ticker = set_xticks
    samples_per_labels = {
        label: str(len(adata[adata.obs["label"] == label])) for label in labels
    }
    samples_per_labels["[  Subset A  ]"] = str(len(hidden_checkbox_A.active))
    samples_per_labels["[  Subset B  ]"] = str(len(hidden_checkbox_B.active))
    samples_per_labels["[  Rest  ]"] = str(len(adata) - len(hidden_checkbox_A.active))
    violins_bokeh_plot.xaxis.major_label_overrides = {
        set_xticks[i]: labels[i] + "\n\n" + samples_per_labels[labels[i]] + "\nsamples" 
        for i in range(len(set_xticks))
    }

    violins_bokeh_plot.visible = True

    # Normalization function for each gene
    def normalize_data(data):
        return (data - np.min(data)) / (np.max(data) - np.min(data) + 1e-6)

    feature_indices_list_ = []
    for idx in features:
        if isinstance(idx, (str, np.str_)):
            assert "var_indices" in adata.uns
            idx = adata.uns["var_indices"][idx]
        feature_indices_list_.append(idx)


    # Prepare subset_indices and label_indices
    last_sample = 0
    set_xticks = []
    label_positions = {}
    label_indices_dict = {}

    if selected_labels is not None:
        
        total_samples= 0
        
        for x,label in enumerate(selected_labels):
            if label == "[  Subset A  ]":
                current_samples = adata.obs.index[hidden_checkbox_A.active].tolist()
                label_indices_dict[label]=current_samples
            elif label == "[  Subset B  ]":
                current_samples = adata.obs.index[hidden_checkbox_B.active].tolist()
                label_indices_dict[label]=current_samples
            elif label == "[  Rest  ]":
                rest_indices = list(set(range(adata.n_obs)) - set(hidden_checkbox_A.active))
                current_samples = adata.obs.index[rest_indices].tolist()
                label_indices_dict[label]=current_samples
            else:
                # Handle standard labels
                current_samples = adata.obs.index[adata.obs["label"] == label].tolist()
                label_indices_dict[label]=current_samples
            # Skip labels with no samples
            if len(current_samples) == 0:
                continue

            # Set label_positions using total_samples for mid-point calculation later
            label_positions[label] = list(range(total_samples, total_samples + len(label_indices_dict[label])))
            total_samples += len(label_indices_dict[label])
         

        # Generate subset_indices from label_indices_dict
        subset_indices_names = [i for label in selected_labels for i in label_indices_dict[label]]
        subset_indices = adata.obs.index.get_indexer(subset_indices_names)
        xsize = len(subset_indices)
        
    else:
        xsize = adata.n_obs
        subset_indices = None


    if xsize == 0:
        print("No data selected for the given labels or feature combination.")
        return  # Exit the function if no data is available

    if "all_labels" not in adata.uns:
        plot_array = np.empty((len(features), xsize))
        for k, idx in enumerate(feature_indices_list_):
            plot_array[k, :] = [adata.X[i, idx] for i in range(adata.n_obs)]
    else:
        (
            list_samples,
            set_xticks,
            label_to_samples_dict,
            set_xticks_text,
            boundaries,
        ) = _samples_by_labels(
            adata,
            sort_annot=True,
            subset_indices=subset_indices,
            equal_size=equal_size,
        )
        if len(list_samples) == 0:
            print("No samples available after filtering by labels.")
            return

        new_adata = adata[list_samples].copy()
        labels = new_adata.obs["label"].unique()
        plot_array = np.empty((len(features), len(list_samples)))
        normalized_plot_array = np.empty_like(plot_array)
        for k, idx in enumerate(feature_indices_list_):
            print(f"Processing feature {features[k]} (index {idx})")
            gene_data = [adata.X[i, idx] for i in list_samples]
            # normalize the data here
            gene_data = normalize_data(gene_data)
            normalized_plot_array[k, :] = gene_data

        if normalized_plot_array.size == 0:
            print("No data available for the selected features and labels.")
            return  # Exit the function if plot_array is empty

    # # HEATMAP
    # # Clear previous renderers
    # heat_map.renderers = []

    # y_positions = {feature: i + 0.5 for i, feature in enumerate(features)}
    # y = [y_positions[feature] for feature in features for _ in range(len(labels))]

    # color_mapper = LinearColorMapper(palette="Viridis256", low=0, high=1)

    # # Prepare data for Rect glyphs
    # x = np.repeat(
    #     np.arange(normalized_plot_array.shape[1]), normalized_plot_array.shape[0]
    # )
    # y = np.tile(
    #     np.arange(normalized_plot_array.shape[0]), normalized_plot_array.shape[1]
    # )
    # colors = [
    #     color_mapper.palette[int(val * (len(color_mapper.palette) - 1))]
    #     for val in normalized_plot_array.T.flatten()
    # ]

    # # Add the Rect glyphs to the plot using the x and y coordinates
    # heat_map.rect(x=x + 0.5, y=y + 0.5, width=1, height=1, color=colors)
    # heat_map.right = []  # Clear existing color bars
    # color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0))
    # heat_map.add_layout(color_bar, "right")

    # heat_map.yaxis.ticker = list(y_positions.values())
    # heat_map.yaxis.major_label_overrides = {v: k for k, v in y_positions.items()}

    # set_xticks = []
    # label_positions = {}
    # last_sample = 0

    # if len(label_indices_dict)>0:

    #     # Update the heatmap with the new ticks and labels
    #     for ab in label_indices_dict.keys():
    #         if len(label_indices_dict) == 1:  # If there's only one label
    #             midpoint = (
    #                 len(label_indices_dict[ab]) / 2
    #             )  # Calculate the midpoint of the range of samples
    #             heat_map.xaxis.ticker = [midpoint]
    #             heat_map.xaxis.major_label_overrides = {
    #                 midpoint: ab
    #             }  # Assign the label to this position
    #             heat_map.visible = True
    #             return
    #         else:
    #             current_samples = list_samples[
    #                 last_sample : last_sample + len(label_indices_dict[ab])
    #             ]
    #             mid_point = last_sample + len(current_samples) / 2
    #             set_xticks.append(mid_point)
    #             label_positions[mid_point] = ab

    #             last_sample += len(current_samples)

    #     heat_map.xaxis.ticker = set_xticks
    #     heat_map.xaxis.major_label_overrides = label_positions
    #     heat_map.xaxis.major_label_orientation = 1.0
    #     heat_map.visible = True

    ### NEW ATTEMPT FOR HEATMAPS

        # # Create evenly spaced x-ticks for each label
        # # num_labels = len(label_to_samples_dict.keys())
        # num_labels = len(labels)
        # print("label_to_samples", label_to_samples_dict)
        # set_xticks = list(range(0, num_labels, 1))

        # heat_map.renderers.clear()  
        # heat_map.right = []         


        # heat_map.xaxis.ticker = set_xticks

    
        # label_keys = list(labels)
        # major_label_overrides_dict = {set_xticks[i]: label_keys[i] for i in range(num_labels)}
        # heat_map.xaxis.major_label_overrides = major_label_overrides_dict

        # # Set the orientation of x-axis labels
        # heat_map.xaxis.major_label_orientation = 1.0
        # heat_map.x_range.start = 0
        # print("set_xticks", set_xticks)
        # heat_map.x_range.end = max(set_xticks)  
        # color_mapper = LinearColorMapper(palette="Viridis256", low=0, high=1)
        # x = np.repeat(
        #     np.arange(normalized_plot_array.shape[1]), normalized_plot_array.shape[0]
        # )
        # y = np.tile(
        #     np.arange(normalized_plot_array.shape[0]), normalized_plot_array.shape[1]
        # )
        # colors = [
        #     color_mapper.palette[int(val * (len(color_mapper.palette) - 1))]
        #     for val in normalized_plot_array.T.flatten()
        # ]

        # heat_map.rect(x=x , y=y, width=1, height=1, color=colors)

        # color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0, 0))
        # heat_map.add_layout(color_bar, "right")
        # y_positions = {feature: i  for i, feature in enumerate(features)}
        # heat_map.yaxis.ticker = list(y_positions.values())
        # heat_map.yaxis.major_label_overrides = {v: k for k, v in y_positions.items()}
        # heat_map.visible = True

def _samples_by_labels(adata, sort_annot=False, subset_indices=None, equal_size=False):

    assert "obs_indices_per_label" in adata.uns and "all_labels" in adata.uns
    if sort_annot:
        argsort_labels = np.argsort(
            [
                len(adata.uns["obs_indices_per_label"][i])
                for i in adata.uns["all_labels"]
            ]
        )[::-1]
    else:
        argsort_labels = np.arange(len(adata.uns["all_labels"]))

    if subset_indices is None:
        if not equal_size:
            i_per_label = adata.uns["obs_indices_per_label"]
        else:
            i_per_label = adata.uns["obs_indices_per_label"].copy()
    else:
        i_per_label = {}
        for lbl in adata.uns["all_labels"]:
            i_per_label[lbl] = []
        for i, annot in enumerate(adata.obs["label"].iloc[subset_indices]):
            i_per_label[annot].append(subset_indices[i])
        for lbl in adata.uns["all_labels"]:
            i_per_label[lbl] = np.array(i_per_label[lbl])

    if equal_size:
        max_size = 0
        for lbl in adata.uns["all_labels"]:
            len_lbl = len(i_per_label[lbl])
            if len_lbl > max_size:
                max_size = len_lbl
        for lbl in adata.uns["all_labels"]:
            tmp_array = np.repeat(
                i_per_label[lbl], int(np.ceil(max_size / len(i_per_label[lbl])))
            )
            rng = np.random.default_rng()
            rng.shuffle(tmp_array)
            i_per_label[lbl] = tmp_array[:max_size]

    list_samples = np.concatenate(
        [i_per_label[adata.uns["all_labels"][i]] for i in argsort_labels]
    ).astype("int")

    boundaries = np.cumsum(
        [0] + [len(i_per_label[adata.uns["all_labels"][i]]) for i in argsort_labels]
    )

    set_xticks2 = (boundaries[1:] + boundaries[:-1]) // 2
    set_xticks = list(np.sort(np.concatenate((boundaries, set_xticks2))))
    set_xticks_text = ["|"] + list(
        np.concatenate([[str(adata.uns["all_labels"][i]), "|"] for i in argsort_labels])
    )

    label_to_samples_dict = {}
    argsort_labels_set = set(argsort_labels)
    label_to_samples_dict = {
        key: value for 
        key, value in label_to_samples_dict.items() if key in argsort_labels_set
    }

    return list_samples, set_xticks, label_to_samples_dict, set_xticks_text, boundaries