import bokeh.models


def subset_buttons(points_bokeh_plot, source_rotmatrix_etc, bt_slider_range):
    source = points_bokeh_plot.select(dict(name="scatterplot"))[0].data_source
    button_width = 112
    # big_button_width = 235

    toggle_A = bokeh.models.Toggle(
        label="Highlight A: ON", width=button_width, active=True
    )
    toggle_B = bokeh.models.Toggle(
        label="Highlight B: ON", width=button_width, active=True
    )

    hidden_checkbox_A = bokeh.models.CheckboxGroup(
        labels=["0"] * len(source.data["name"]), active=[]
    )

    hidden_checkbox_B = bokeh.models.CheckboxGroup(
        labels=["0"] * len(source.data["name"]), active=[]
    )

    size_redef_code = """
        point_s[i] = point_s_ref[i] * size_coef[0] * (
            2.5 * Math.max(hA[i], hB[i]) + 1.0);
        line_c[i] = -1. + hA[i] * 0.25 + hB[i] * 0.90;
        line_w[i] = point_s_ref[i] * size_coef[0] * 0.85 * Math.max(
            hA[i], hB[i]);
    """

    toggle_A.js_on_change(
        "active",
        bokeh.models.CustomJS(
            args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
            code="""
        const data = source.data;
        const data_rotmatrix_etc = source_rotmatrix_etc.data;
        const hA = data['highlighted_A'];
        const hB = data['highlighted_B'];
        const sA = data['subset_A'];
        const point_s = data['point_size'];
        const point_s_ref = data['point_size_ref'];
        const line_c = data['line_color'];
        const line_w = data['line_width'];
        const size_coef = data_rotmatrix_etc['size_coef'];
        if (this.active) {
            this.label = 'Highlight A: ON';
            for (let i = 0; i < hA.length; i++) {
                hA[i] = sA[i];"""
            + size_redef_code
            + """
            }
        } else {
            this.label = 'Highlight A: OFF';
            for (let i = 0; i < hA.length; i++) {
                hA[i] = 0.;"""
            + size_redef_code
            + """
            }
        }
        source.change.emit();
    """,
        ),
    )
    toggle_B.js_on_change(
        "active",
        bokeh.models.CustomJS(
            args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
            code="""
        const data = source.data;
        const data_rotmatrix_etc = source_rotmatrix_etc.data;
        const hB = data['highlighted_B'];
        const hA = data['highlighted_A'];
        const sB = data['subset_B'];
        const point_s = data['point_size'];
        const point_s_ref = data['point_size_ref'];
        const line_c = data['line_color'];
        const line_w = data['line_width'];
        const size_coef = data_rotmatrix_etc['size_coef'];
        if (this.active) {
            this.label = 'Highlight B: ON';
            for (let i = 0; i < hB.length; i++) {
                hB[i] = sB[i];"""
            + size_redef_code
            + """
            }
        } else {
            this.label = 'Highlight B: OFF';
            for (let i = 0; i < hB.length; i++) {
                hB[i] = 0.;"""
            + size_redef_code
            + """
            }
        }
        source.change.emit();
    """,
        ),
    )

    callback_AB_part_1 = """
        const indices = source.selected.indices;
        const data = source.data;
        const data_rotmatrix_etc = source_rotmatrix_etc.data;
        const point_s = data['point_size'];
        const point_s_ref = data['point_size_ref'];
        const sA = data['subset_A'];
        const sB = data['subset_B'];
        const hA = data['highlighted_A'];
        const hB = data['highlighted_B'];
        const line_c = data['line_color'];
        const line_w = data['line_width'];
        const size_coef = data_rotmatrix_etc['size_coef'];
        for (let i = 0; i < point_s.length; i++) {
    """
    callback_AB_part_2 = (
        size_redef_code
        + """
        }

        source.change.emit();
        toggle.active=true;
    """
    )

    callback_js_A = bokeh.models.CustomJS(
        args=dict(
            source=source,
            source_rotmatrix_etc=source_rotmatrix_etc,
            toggle=toggle_A,
            cbx=hidden_checkbox_A,
            cbx_other=hidden_checkbox_B,
        ),
        code=callback_AB_part_1
        + """
            sA[i] = 0.;
        }
        var t = [];
        var t_remove = [];
        for (let i = 0; i < indices.length; i++) {
            sA[indices[i]] = 1.;
            if (sB[indices[i]] == 1.) {
                t_remove.push(data["index"][indices[i]]);
            }
            sB[indices[i]] = 0.;
            hB[indices[i]] = 0.;
            t.push(data["index"][indices[i]]);
        }
        if (t_remove.length > 0) {
            let difference = cbx_other.active.filter(x => !t_remove.includes(x));
            cbx_other.active = difference;
            cbx_other.change.emit();
        }
        cbx.active = t;
        cbx.change.emit();
        const t_active = toggle.active;
        for (let i = 0; i < point_s.length; i++) {
            if (t_active) {
                hA[i] = sA[i];
            }
        """
        + callback_AB_part_2,
    )

    callback_js_B = bokeh.models.CustomJS(
        args=dict(
            source=source,
            source_rotmatrix_etc=source_rotmatrix_etc,
            toggle=toggle_B,
            cbx=hidden_checkbox_B,
            cbx_other=hidden_checkbox_A,
        ),
        code=callback_AB_part_1
        + """
            sB[i] = 0.;
        }
        var t = [];
        var t_remove = [];
        for (let i = 0; i < indices.length; i++) {
            sB[indices[i]] = 1.;
            if (sA[indices[i]] == 1.) {
                t_remove.push(data["index"][indices[i]]);
            }
            sA[indices[i]] = 0.;
            hA[indices[i]] = 0.;
            t.push(data["index"][indices[i]]);
        }
        if (t_remove.length > 0) {
            let difference = cbx_other.active.filter(x => !t_remove.includes(x));
            cbx_other.active = difference;
            cbx_other.change.emit();
        }
        cbx.active = t;
        cbx.change.emit();
        const t_active = toggle.active;
        for (let i = 0; i < point_s.length; i++) {
            if (t_active) {
                hB[i] = sB[i];
            }
        """
        + callback_AB_part_2,
    )

    bt_A = bokeh.models.Button(
        label="Set subset A", width=button_width, button_type="primary"
    )
    bt_B = bokeh.models.Button(
        label="Set subset B", width=button_width, button_type="danger"
    )

    bt_A.js_on_click(callback_js_A)
    bt_B.js_on_click(callback_js_B)

    bt_AplusB = bokeh.models.Button(label="Select A+B", width=button_width)
    bt_AplusB.js_on_click(
        bokeh.models.CustomJS(
            args=dict(source=source),
            code="""
        const data = source.data;
        var t = [];
        const sA = data['subset_A'];
        const sB = data['subset_B'];
        const point_s = data['point_size'];
        for (let i = 0; i < point_s.length; i++) {
            if (sB[i] == 1. || sA[i] == 1.) {
                t.push(i);
            }
        }
        source.selected.indices = t;
        source.change.emit();
    """,
        )
    )

    bt_nothing = bokeh.models.Button(label="Select nothing", width=button_width)
    bt_nothing.js_on_click(
        bokeh.models.CustomJS(
            args=dict(source=source, btsr=bt_slider_range),
            code="""
        const data = source.data;
        source.selected.indices = [];
        source.change.emit();
        btsr.value = [btsr.start, btsr.end];
        btsr.change.emit();
    """,
        )
    )

    return (
        bt_A,
        toggle_A,
        hidden_checkbox_A,
        bt_B,
        toggle_B,
        hidden_checkbox_B,
        bt_AplusB,
        bt_nothing,
    )
