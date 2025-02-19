import yomix.plotting
import yomix.tools
import bokeh.layouts
from bokeh.models import TabPanel, Tabs
import yomix
import numpy as np
import anndata
from scipy.sparse import issparse
import os


def gen_modify_doc(filearg, subsampling, title):

    xd = anndata.read_h5ad(filearg.absolute())

    def _to_dense(x):
        if issparse(x):
            return x.todense()
        else:
            return x

    xd.X = np.asarray(_to_dense(xd.X))

    if subsampling is not None:
        if xd.n_obs > subsampling:
            selected_obs = np.random.choice(xd.n_obs, subsampling, replace=False)
            selected_obs.sort()
            xd = xd[selected_obs].copy()

    min_norm = np.min(xd.X, axis=0)
    max_norm = np.max(xd.X, axis=0)
    xd.X = np.divide(xd.X - min_norm, max_norm - min_norm + 1e-8)
    obs_string_init = list(xd.obs.select_dtypes("category").keys())
    all_labels_list = []
    for lbl in sorted(obs_string_init):
        # filter labels
        if yomix.plotting.check_obs_field(xd, str(lbl)):
            labels = np.array(list(dict.fromkeys(xd.obs[str(lbl)])))
            all_labels_list += [(str(lbl), str(elt)) for elt in sorted(labels)]
            for elt in labels:
                xd.var["yomix_median_" + str(lbl) + ">>yomix>>" + str(elt)] = -np.ones(
                    xd.n_vars
                )
    xd.uns["all_labels"] = all_labels_list

    def var_mean_values(adata) -> np.ndarray:
        return np.squeeze(np.asarray(np.mean(adata.X, axis=0)))

    def var_standard_deviations(adata) -> np.ndarray:
        return np.squeeze(np.asarray(np.std(adata.X, axis=0)))

    xd.var["mean_values_local_yomix"] = var_mean_values(xd)
    xd.var["standard_deviations_local_yomix"] = var_standard_deviations(xd)
    xd.var_names_make_unique()
    xd.obs_names_make_unique()

    def modify_doc(doc):

        def build_figure(embedding_key):

            if embedding_key is None:
                embedding_key = ""

            list_ok_embed_keys = []
            for k in xd.obsm.keys():
                if xd.obsm[k].shape[1] > 1:
                    list_ok_embed_keys.append(k)

            bt_select_embedding = bokeh.models.Select(
                title="Select embedding (.obsm field)",
                value=embedding_key,
                width=235,
                options=[(k, k) for k in list_ok_embed_keys],
                name="bt_select_embedding",
            )

            if embedding_key != "":

                embedding_size = xd.obsm[embedding_key].shape[1]
                assert embedding_size > 1

                (
                    obs_string,
                    obs_numerical,
                    points_bokeh_plot,
                    violins_bokeh_plot,
                    heat_map,
                    bt_slider_point_size,
                    bt_hidden_slider_yaw,
                    bt_slider_range,
                    bt_toggle_anim,
                    bt_slider_yaw,
                    bt_slider_pitch,
                    bt_slider_roll,
                    resize_width_input,
                    resize_height_input,
                    resize_width_input_bis,
                    resize_height_input_bis,
                    source_rotmatrix_etc,
                    div_sample_names,
                    sample_search_input,
                    sl_component1,
                    sl_component2,
                    sl_component3,
                ) = yomix.plotting.main_figure(xd, embedding_key, 890, 390, title)

                resize_width_input_bis.visible = False
                resize_height_input_bis.visible = False

                (
                    bt_A,
                    toggle_A,
                    hidden_checkbox_A,
                    bt_B,
                    toggle_B,
                    hidden_checkbox_B,
                    bt_AplusB,
                    bt_nothing,
                ) = yomix.tools.subset_buttons(
                    points_bokeh_plot, source_rotmatrix_etc, bt_slider_range
                )

                (
                    select_color_by,
                    help_color_by,
                    hidden_text_label_column,
                    hidden_legend_width,
                ) = yomix.plotting.setup_legend(
                    points_bokeh_plot,
                    obs_string,
                    obs_numerical,
                    source_rotmatrix_etc,
                    resize_width_input,
                    bt_slider_range,
                )

                offset_text_feature_color, offset_label = (
                    yomix.plotting.color_by_feature_value(
                        points_bokeh_plot,
                        violins_bokeh_plot,
                        heat_map,
                        xd,
                        select_color_by,
                        hidden_text_label_column,
                        resize_width_input,
                        hidden_legend_width,
                        hidden_checkbox_A,
                        hidden_checkbox_B,
                        resize_width_input_bis,
                        resize_height_input_bis,
                        bt_slider_range,
                    )
                )
                offset_label.visible = False

                (
                    bt_sign1,
                    bt_sign2,
                    help1,
                    help2,
                    multiselect_signature,
                    div_signature_list,
                    sign_nr,
                    label_signature,
                ) = yomix.tools.signature_buttons(
                    xd,
                    offset_text_feature_color,
                    offset_label,
                    hidden_checkbox_A,
                    hidden_checkbox_B,
                )

                select_color_by.js_on_change(
                    "value",
                    bokeh.models.CustomJS(
                        args=dict(
                            otfc=offset_text_feature_color, ms=multiselect_signature
                        ),
                        code="""
                            if (cb_obj.value != "") {
                                otfc.value="";
                                ms.value=[];
                            }
                        """,
                    ),
                )

                bt_open_link = yomix.tools.gene_query_button(offset_text_feature_color)

                bt_sign3, help3 = yomix.tools.arrow_function(
                    points_bokeh_plot,
                    xd,
                    embedding_key,
                    bt_slider_roll,
                    bt_slider_pitch,
                    bt_slider_yaw,
                    source_rotmatrix_etc,
                    bt_toggle_anim,
                    hidden_checkbox_A,
                    div_signature_list,
                    multiselect_signature,
                    sign_nr,
                    sl_component1,
                    sl_component2,
                    sl_component3,
                    label_signature,
                )

                c1div = bokeh.models.Div(text="X axis:")
                c2div = bokeh.models.Div(text="Y axis:")
                c3div = bokeh.models.Div(text="Z axis:")

                if embedding_size == 2:
                    bt_slider_yaw.visible = False
                    bt_slider_pitch.visible = False
                    bt_toggle_anim.visible = False
                    bt_toggle_anim.active = False
                    c3div.visible = False

                violins_bokeh_plot.toolbar.logo = None
                violins_bokeh_plot.toolbar_location = None
                heat_map.toolbar.logo = None
                heat_map.toolbar_location = None

                tabs = Tabs(
                    tabs=[
                        TabPanel(child=violins_bokeh_plot, title="Violin plots"),
                        TabPanel(child=heat_map, title="Heatmap"),
                    ]
                )

                p = bokeh.layouts.row(
                    bokeh.layouts.column(
                        bt_select_embedding,
                        bokeh.layouts.row(bt_A, toggle_A),
                        bokeh.layouts.row(bt_B, toggle_B),
                        bokeh.layouts.row(bt_nothing, bt_AplusB),
                        bokeh.layouts.row(bt_sign1, help1),
                        bokeh.layouts.row(bt_sign2, help2),
                        bokeh.layouts.row(bt_sign3, help3),
                        multiselect_signature,
                        label_signature,
                        div_signature_list,
                    ),
                    (
                        bokeh.layouts.column(
                            bokeh.layouts.row(
                                bokeh.layouts.column(c1div, c2div, c3div),
                                bokeh.layouts.column(
                                    sl_component1, sl_component2, sl_component3
                                ),
                            ),
                            bokeh.layouts.row(
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        bt_slider_roll,
                                        bt_slider_yaw,
                                        bt_toggle_anim,
                                    ),
                                    bt_slider_pitch,
                                    bt_slider_point_size,
                                ),
                                bokeh.layouts.column(
                                    bokeh.layouts.row(
                                        select_color_by,
                                        help_color_by,
                                        sample_search_input,
                                    ),
                                    bokeh.layouts.row(
                                        offset_text_feature_color, bt_open_link
                                    ),
                                ),
                            ),
                            bokeh.layouts.column(
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        resize_height_input, resize_width_input
                                    ),
                                    points_bokeh_plot,
                                    bt_slider_range,
                                ),
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        resize_height_input_bis,
                                        resize_width_input_bis,
                                    ),
                                    tabs,
                                    div_sample_names,
                                ),
                            ),
                            offset_label,
                        )
                        if sl_component1 is not None
                        else bokeh.layouts.column(
                            bokeh.layouts.row(
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        bt_slider_roll,
                                        bt_slider_yaw,
                                        bt_toggle_anim,
                                    ),
                                    bt_slider_pitch,
                                    bt_slider_point_size,
                                ),
                                bokeh.layouts.column(
                                    bokeh.layouts.row(
                                        select_color_by,
                                        help_color_by,
                                        sample_search_input,
                                    ),
                                    bokeh.layouts.row(
                                        offset_text_feature_color, bt_open_link
                                    ),
                                ),
                            ),
                            bokeh.layouts.column(
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        resize_height_input, resize_width_input
                                    ),
                                    points_bokeh_plot,
                                    bt_slider_range,
                                ),
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        resize_height_input_bis,
                                        resize_width_input_bis,
                                    ),
                                    tabs,
                                    div_sample_names,
                                ),
                            ),
                            offset_label,
                        )
                    ),
                    bt_hidden_slider_yaw,
                )

            else:
                p = bokeh.layouts.row(bt_select_embedding)

            p.name = "root"
            return p

        def reset_figure(new):
            doc.clear()
            p_new = build_figure(new)
            p_new.select_one(dict(name="bt_select_embedding")).on_change(
                "value", lambda attr, old, new: reset_figure(new)
            )
            doc.add_root(p_new)

        p_0 = build_figure(None)
        p_0.select_one(dict(name="bt_select_embedding")).on_change(
            "value", lambda attr, old, new: reset_figure(new)
        )

        doc.add_root(p_0)

        def f():
            slider = doc.get_model_by_name("root").select_one(
                dict(name="bt_hidden_slider_yaw")
            )
            anim = doc.get_model_by_name("root").select_one(dict(name="bt_toggle_anim"))
            # print(slider)
            if slider is not None and anim.active:
                slider.value = 10

        doc.add_periodic_callback(f, 100)

        doc.title = f"Yomix - {os.path.basename(filearg)}"

    return modify_doc
