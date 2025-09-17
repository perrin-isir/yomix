# """
# This module provides a unique feature that allows users to explore data along
# a user-defined trajectory or gradient. It adds an interactive arrow tool to the
# main plot, enabling the user to draw a vector directly on the embedding. The
# module can then compute an "oriented signature" by identifying the features
# whose values are most strongly correlated either positively or negatively
# with the direction of the arrow. This is particularly useful for analyzing
# continuous biological processes, such as cell differentiation or activation.
# """

from pathlib import Path
import pandas as pd
import bokeh.models
import numpy as np
import anndata


def arrow_function(
    points_bokeh_plot: bokeh.plotting.figure,
    adata: anndata.AnnData,
    embedding_key: str,
    bt_slider_roll: bokeh.models.Slider,
    bt_slider_pitch: bokeh.models.Slider,
    bt_slider_yaw: bokeh.models.Slider,
    source_rotmatrix_etc: bokeh.models.ColumnDataSource,
    bt_toggle_anim: bokeh.models.Toggle,
    hidden_checkbox_A: bokeh.models.CheckboxGroup,
    div_signature_list: bokeh.models.Div,
    multiselect_signature: bokeh.models.MultiSelect,
    sign_nr: list,
    sl_component1: bokeh.models.RadioButtonGroup,
    sl_component2: bokeh.models.RadioButtonGroup,
    sl_component3: bokeh.models.RadioButtonGroup,
    label_sign: bokeh.models.MultiSelect,
) -> tuple[bokeh.models.Button, bokeh.models.HelpButton]:
    """
    Create and manage the arrow tool for oriented signature analysis
    Add the "Arrow Tool" to the Bokeh scatter plot that lets the user draw an arrow
    (start and end points). The arrow direction is then used to compute
    an *oriented signature*: a set of features most correlated with the
    arrow direction in the embedding space.

    Args:
        points_bokeh_plot (bokeh.plotting.figure):
            Bokeh scatter plot of observations.
        adata (anndata.AnnData):
            Annotated data matrix of shape `n_obs` x `n_vars`.
        embedding_key (str):
            Key in ``adata.obsm`` storing the embedding coordinates.
        bt_slider_yaw (bokeh.models.Slider):
            Slider button that controls yaw rotation.
        bt_slider_pitch (bokeh.models.Slider):
            Slider button that controls pitch rotation.
        bt_slider_roll (bokeh.models.Slider):
            Slider button that controls roll rotation.
        source_rotmatrix_etc (bokeh.models.ColumnDataSource):
            Data source for computing points' positions after rotations in the scatterplot.
        bt_toggle_anim (bokeh.models.Toggle):
            Toggle controlling animation state.
        hidden_checkbox_A (bokeh.models.CheckboxGroup):
            Widget storing "Subset A" sample indices.
        div_signature_list (bokeh.models.Div):
            Div displaying most correlated features from the computed signature.
        multiselect_signature (bokeh.models.MultiSelect):
            MultiSelect widget listing most correlated features from the computed signature.
        sign_nr (list):
            A list containing an single integer to count the number of signatures that were computed.
        sl_component1 (bokeh.models.RadioButtonGroup):
            Button to select which dimension should be used for the x-axis.
        sl_component2 (bokeh.models.RadioButtonGroup):
            Button to select which dimension should be used for the y-axis.
        sl_component3 (bokeh.models.RadioButtonGroup):
            Button to select which dimension should be used for the z-axis.
        label_sign (bokeh.models.MultiSelect):
            Widget for selecting groups in violin plots / heat map.

    Returns:
        Tuple containing the Bokeh widgets created by this function
            - **bt_sign_oriented** (:class:`bokeh.models.Button`): Button that triggers oriented signature computation based on the drawn arrow.
            - **help_button_oriented** (:class:`bokeh.models.HelpButton`): Tooltip button describing requirements for computing oriented signatures.
    """  # noqa

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
        adata: anndata.AnnData,
        embedding_key: str,
        obs_indices_A: list[int],
        dir_x: float,
        dir_y: float,
        hidden_num_in: list[bokeh.models.NumericInput],
    ) -> tuple[np.ndarray, dict, dict]:
        """
        Compute the oriented signature for a subset of observations along a
        user-defined arrow direction.

        Parameters:
            adata : anndata.AnnData
                Annotated data matrix.
            embedding_key : str
                Key in `adata.obsm` storing the embedding coordinates.
            obs_indices_A : list of int
                Indices of observations in subset A.
            dir_x : float
                X component of the arrow direction.
            dir_y : float
                Y component of the arrow direction.
            hidden_num_in : list of bokeh.models.NumericInput
                List of hidden numeric input widgets containing rotation matrix values.

        Returns:
            tuple
                - sorted_features: np.ndarray
                    Indices of the top correlated features.
                - corr_dict: dict
                    Dictionary mapping feature indices to correlation scores.
                - up_or_down_dict: dict
                    Dictionary mapping feature indices to "+" or "-" depending on
                    correlation sign.
        """
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
        ad: anndata.AnnData,
        embedding_key: str,
        arr_layout: bokeh.models.Arrow,
        obs_indices_A: list[int],
        dv: bokeh.models.Div,
        ms_sign: bokeh.models.MultiSelect,
        sign_nr: list[int],
        hidden_num_in: list[bokeh.models.NumericInput],
    ) -> None:
        """
        Compute and display the oriented signature for subset A based on the drawn
        arrow.

        Parameters:
            ad : anndata.AnnData
                Annotated data matrix.
            embedding_key : str
                Key in `ad.obsm` storing the embedding coordinates.
            arr_layout : bokeh.models.Arrow
                Arrow layout object representing the user-drawn arrow.
            obs_indices_A : list of int
                Indices of observations in subset A.
            dv : bokeh.models.Div
                Div widget to display the signature.
            ms_sign : bokeh.models.MultiSelect
                MultiSelect widget to list signature features.
            sign_nr : list of int
                List containing a single integer tracking the number of computed
                signatures.
            hidden_num_in : list of bokeh.models.NumericInput
                List of hidden numeric input widgets containing rotation matrix values.

        Returns:
            None
        """

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
