from pathlib import Path
import pandas as pd
import bokeh.models
import numpy as np


def arrow_function(
    points_bokeh_plot,
    adata,
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
    label_sign,
):

    arrow_clicks = bokeh.models.ColumnDataSource(data=dict(x=[], y=[]))

    arrow = bokeh.models.Arrow(
        end=bokeh.models.OpenHead(line_color="darkgray", line_width=4),
        line_color="darkgray",
        line_width=4,
        x_start=0.0,
        x_end=0.0,
        y_start=0.0,
        y_end=0.0,
        name="arrow",
        visible=False,
    )

    points_bokeh_plot.add_layout(arrow)

    def callback_arrow(event):
        if arrow.visible:
            if len(arrow_clicks.data["x"]) == 0:
                arrow_clicks.stream(dict(x=[event.x], y=[event.y]))
            else:
                arrow.x_start, arrow.y_start = (
                    arrow_clicks.data["x"][0],
                    arrow_clicks.data["y"][0],
                )
                arrow.x_end, arrow.y_end = event.x, event.y
                arrow_clicks.data = dict(x=[], y=[])

    points_bokeh_plot.on_event(bokeh.events.Tap, callback_arrow)

    hidden_toggle = bokeh.models.Toggle(name="hidden_toggle", active=False)

    arrow_tool = bokeh.models.CustomAction(
        description="Arrow Tool: click once for the start, twice for the end" "",
        icon=(Path(__file__).parent.parent / "assets" / "arrow.png").absolute(),
        callback=bokeh.models.CustomJS(
            args=dict(arr=arrow, hidden_t=hidden_toggle, btta=bt_toggle_anim),
            code="""
        btta.active=false;
        hidden_t.active=!hidden_t.active;
    """,
        ),
    )
    points_bokeh_plot.add_tools(arrow_tool)

    def toggle_arrow(new):
        if new:
            arrow_tool.icon = (
                Path(__file__).parent.parent / "assets" / "arrow_pressed.png"
            ).absolute()
            delta_x = (
                points_bokeh_plot.x_range.end - points_bokeh_plot.x_range.start
            ) / 4.0
            delta_y = (
                points_bokeh_plot.y_range.end - points_bokeh_plot.y_range.start
            ) / 4.0
            arrow.x_start = points_bokeh_plot.x_range.start + delta_x
            arrow.y_start = points_bokeh_plot.y_range.start + delta_y
            arrow.x_end = points_bokeh_plot.x_range.end - delta_x
            arrow.y_end = points_bokeh_plot.y_range.end - delta_y
            arrow.visible = True
        else:
            arrow_tool.icon = (
                Path(__file__).parent.parent / "assets" / "arrow.png"
            ).absolute()
            arrow.visible = False

    hidden_toggle.on_change("active", lambda attr, old, new: toggle_arrow(new))

    def rotations_deactivate_arrow():
        if hidden_toggle.active:
            hidden_toggle.active = False

    def toggle_rotations_deactivate_arrow(new):
        if new:
            if hidden_toggle.active:
                hidden_toggle.active = False

    bt_slider_roll.on_change(
        "value", lambda attr, old, new: rotations_deactivate_arrow()
    )
    bt_slider_pitch.on_change(
        "value", lambda attr, old, new: rotations_deactivate_arrow()
    )
    bt_slider_yaw.on_change(
        "value", lambda attr, old, new: rotations_deactivate_arrow()
    )
    bt_toggle_anim.on_change(
        "active", lambda attr, old, new: toggle_rotations_deactivate_arrow(new)
    )

    hidden_numeric_inputs = [
        bokeh.models.NumericInput(mode="float", value=0.0) for _ in range(10)
    ]

    tooltip = bokeh.models.Tooltip(
        content="Requires drawing an arrow with the Arrow Tool "
        "and setting subset A.\u00A0\u00A0",
        position="right",
    )
    help_button_oriented = bokeh.models.HelpButton(tooltip=tooltip, margin=(3, 0, 3, 0))
    bt_sign_oriented = bokeh.models.Button(
        label="Compute oriented signature (A)", width=190, margin=(5, 0, 5, 5)
    )

    bt_sign_oriented.js_on_click(
        bokeh.models.CustomJS(
            args=dict(
                source_rotmatrix_etc=source_rotmatrix_etc,
                numinputs=hidden_numeric_inputs,
                ht=hidden_toggle,
            ),
            code="""
            if (ht.active) {
                numinputs[0].value=source_rotmatrix_etc.data['0'][0];
                numinputs[1].value=source_rotmatrix_etc.data['0'][1];
                numinputs[2].value=source_rotmatrix_etc.data['0'][2];
                numinputs[3].value=source_rotmatrix_etc.data['1'][0];
                numinputs[4].value=source_rotmatrix_etc.data['1'][1];
                numinputs[5].value=source_rotmatrix_etc.data['1'][2];
                numinputs[6].value=source_rotmatrix_etc.data['2'][0];
                numinputs[7].value=source_rotmatrix_etc.data['2'][1];
                numinputs[8].value=source_rotmatrix_etc.data['2'][2];
                numinputs[9].value+=1.;
            }
        """,
        )
    )

    def compute_oriented_signature(
        adata, embedding_key, obs_indices_A, dir_x, dir_y, hidden_num_in
    ):
        rotmatrix = np.array([inpt.value for inpt in hidden_num_in[:9]]).reshape(3, 3)
        points_in_A = np.asarray(adata.obsm[embedding_key][obs_indices_A])
        if points_in_A.shape[1] > 2:
            if sl_component1 is None:
                points3d = points_in_A[:, :3]
            else:
                points3d = points_in_A[
                    :,
                    [
                        max(sl_component1.active - 1, 0),
                        max(sl_component2.active - 1, 0),
                        max(sl_component3.active - 1, 0),
                    ],
                ].copy()
                if sl_component1.active == 0:
                    points3d[:, 0] = 0.0
                if sl_component2.active == 0:
                    points3d[:, 1] = 0.0
                if sl_component3.active == 0:
                    points3d[:, 2] = 0.0
        else:
            points3d = np.hstack(
                (points_in_A, np.zeros((len(points_in_A), 1), dtype=np.float32))
            )
        coords = np.dot(rotmatrix, points3d.T).T
        components = dir_x * coords[:, 0] + dir_y * coords[:, 1]
        # corr_scores = []
        # for i in range(adata.n_vars):
        #     a = adata.X[obs_indices_A, i]
        #     try:
        #         res = stats.pearsonr(a, components)
        #     except stats.ConstantInputWarning:
        #         pass
        #     corr_scores.append(np.abs(res.statistic))

        a = pd.DataFrame(adata.X[obs_indices_A, :])
        b = pd.DataFrame(np.tile(components, (a.shape[1], 1)).T)
        corr_scores = a.corrwith(b).to_numpy()
        # corr_scores = np.abs(corr_scores)
        corr_scores = np.vectorize(lambda x: 0.0 if np.isnan(x) else x)(corr_scores)
        sorted_features = np.argsort(np.abs(corr_scores))[::-1][:20]
        cscores = corr_scores[sorted_features]
        corr_dict = dict(map(lambda i, j: (i, j), sorted_features, cscores))
        up_or_down_dict = dict(
            map(lambda i, j: (i, "+" if j >= 0.0 else "-"), sorted_features, cscores)
        )
        return sorted_features, corr_dict, up_or_down_dict

    # TODO remove redundancy (shrink_test is defined twice)
    def shrink_text(s_in, size):
        true_size = max(size, 3)
        if len(s_in) > true_size:
            new_s = ""
            l1 = true_size // 2
            l2 = true_size - l1 - 3
            new_s += s_in[:l1]
            new_s += "..."
            new_s += s_in[-l2:]
        else:
            new_s = s_in
        return new_s

    def oriented_sign_A(
        ad,
        embedding_key,
        arr_layout,
        obs_indices_A,
        dv,
        ms_sign,
        sign_nr,
        hidden_num_in,
    ):
        # print(arr_layout.x_start, arr_layout.y_end, arr_layout.y_start)
        if 0 < len(obs_indices_A) and (
            arr_layout.x_end != arr_layout.x_start
            or arr_layout.y_end != arr_layout.y_start
        ):
            ms_sign.title = "..."
            outputs, corr_dict, up_or_down_dict = compute_oriented_signature(
                ad,
                embedding_key,
                obs_indices_A,
                arr_layout.x_end - arr_layout.x_start,
                arr_layout.y_end - arr_layout.y_start,
                hidden_num_in,
            )
            sign_nr[0] += 1
            dv.text = (
                "Signature #"
                + str(sign_nr[0])
                + ": "
                + ", ".join(['<b>"' + elt + '"</b>' for elt in ad.var_names[outputs]])
            )
            ms_sign.options = [
                (
                    up_or_down_dict[outp] + ad.var_names[outp],
                    up_or_down_dict[outp]
                    + " (Corr.:{:.3f}) ".format(corr_dict[outp])
                    + shrink_text(ad.var_names[outp], 25),
                )
                for outp in outputs
            ]
            ms_sign.title = "Signature #" + str(sign_nr[0])

            unique_labels = []
            unique_labels.append(("[  Subset A  ]", "[  Subset A  ]"))
            unique_labels.append(("[  Rest  ]", "[  Rest  ]"))
            unique_labels += [
                (lbl + ">>yomix>>" + lbl_elt, shrink_text(lbl + " > " + lbl_elt, 35))
                for (lbl, lbl_elt) in ad.uns["all_labels"]
            ]

            # Update label_sign options
            label_sign.options = unique_labels
            label_sign.size = len(label_sign.options)
            # finalize label_sign
            label_sign.title = "Groups"
            label_sign.value = ["[  Subset A  ]", "[  Rest  ]"]

    hidden_numeric_inputs[9].on_change(
        "value",
        lambda attr, old, new: oriented_sign_A(
            adata,
            embedding_key,
            arrow,
            hidden_checkbox_A.active,
            div_signature_list,
            multiselect_signature,
            sign_nr,
            hidden_numeric_inputs,
        ),
    )

    return bt_sign_oriented, help_button_oriented
