import numpy as np
import bokeh.models
import bokeh.io
import bokeh.layouts
import re
from bokeh.models import (
    HoverTool,
    LassoSelectTool,
    WheelZoomTool,
    ResetTool,
    HelpTool,
    InlineStyleSheet,
    Range1d,
)
from bokeh.models.tools import CustomAction
import bokeh.plotting as bkp
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

MAX_UNIQUE_VALUES = 200
MAX_UNIQUE_RATIO = 0.5


def check_obs_field(xd, field):
    unique_items_nr = len(xd.obs[field].unique())
    return (
        unique_items_nr < MAX_UNIQUE_VALUES
        and unique_items_nr / xd.n_obs <= MAX_UNIQUE_RATIO
    )


def main_figure(adata, embedding_key, width=900, height=600, title=""):

    obs_string = [
        x
        for x in list(adata.obs.select_dtypes(include=["category", "object"]).keys())
        if check_obs_field(adata, x)
    ]
    obs_numerical = list(adata.obs.select_dtypes(np.number).keys())

    embedding_size = adata.obsm[embedding_key].shape[1]

    if embedding_size > 3:
        higher_dim = True
    else:
        higher_dim = False

    tooltip_list = []
    data = {
        "x": np.asarray(adata.obsm[embedding_key][:, 0], dtype=np.float32).copy(),
        "y": np.asarray(adata.obsm[embedding_key][:, 1], dtype=np.float32).copy(),
        "color": np.zeros(len(adata.obsm[embedding_key]), dtype=np.float32),
        "index": np.zeros(len(adata.obsm[embedding_key]), dtype=int),
        "name": np.full(len(adata.obsm[embedding_key]), "", dtype=object),
    }
    if embedding_size >= 3:
        data["z"] = np.asarray(adata.obsm[embedding_key][:, 2], dtype=np.float32).copy()
    else:
        data["z"] = np.zeros_like(data["x"], dtype=np.float32).copy()
    for i in range(len(data["x"])):
        data["index"][i] = i
        data["name"][i] = adata.obs_names[i]
    # tooltip_list.append("index")
    tooltip_list.append("name")
    for key in adata.obs.keys():
        if key not in ("name", "index"):
            data[key] = np.asarray(adata.obs[key])
            tooltip_list.append(key)
    for i in range(embedding_size):
        data["original_embedding_" + str(i)] = np.asarray(
            adata.obsm[embedding_key][:, i], dtype=np.float32
        )

    if title == "":
        title = (
            "Yomix " + Path(__file__).parent.with_name("VERSION").read_text().strip()
        )
    xyz_vectors = np.vstack((data["x"], data["y"], data["z"]))
    true_center = np.array([[data["x"].mean(), data["y"].mean(), data["z"].mean()]]).T
    xyz_norms = np.linalg.norm(xyz_vectors - true_center, axis=0)
    xyz_max = xyz_norms.max()
    x_min = data["x"].min()
    x_max = data["x"].max()
    y_min = data["y"].min()
    y_max = data["y"].max()

    data["point_size"] = data["z"].copy()
    for i in range(len(data["point_size"])):
        data["point_size"][i] = 5.0 / (
            1.0
            + np.exp(
                min(
                    max(
                        (-data["point_size"][i] + true_center[2, 0])
                        / (xyz_max + 0.0000001),
                        -1.0,
                    ),
                    1.0,
                )
            )
        )

    data["x_saved"] = data["x"].copy()
    data["y_saved"] = data["y"].copy()
    data["z_saved"] = data["z"].copy()
    data["point_size_ref"] = data["point_size"].copy()
    data["color_ref"] = data["color"].copy()

    data["subset_A"] = np.zeros(len(data["point_size"]), dtype=np.float32)
    data["subset_B"] = np.zeros(len(data["point_size"]), dtype=np.float32)
    data["highlighted_A"] = np.zeros(len(data["point_size"]), dtype=np.float32)
    data["highlighted_B"] = np.zeros(len(data["point_size"]), dtype=np.float32)
    data["line_color"] = -np.ones(len(data["point_size"]), dtype=np.float32)
    data["line_width"] = np.zeros(len(data["point_size"]), dtype=np.float32)

    source = bokeh.models.ColumnDataSource(data=data)

    points_bokeh_plot = bkp.figure(
        width=width,
        height=height,
        title=title,
        x_axis_type="linear",
        y_axis_type="linear",
        toolbar_location="left",
    )
    points_bokeh_plot.xgrid.grid_line_color = None
    points_bokeh_plot.ygrid.grid_line_color = None
    points_bokeh_plot.xaxis.axis_label = ""
    points_bokeh_plot.yaxis.axis_label = ""
    points_bokeh_plot.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    points_bokeh_plot.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    points_bokeh_plot.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    points_bokeh_plot.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    points_bokeh_plot.xaxis.major_label_text_font_size = (
        "0pt"  # preferred method for removing tick labels
    )
    points_bokeh_plot.yaxis.major_label_text_font_size = (
        "0pt"  # preferred method for removing tick labels
    )
    points_bokeh_plot.x_range = Range1d(x_min, x_max)
    points_bokeh_plot.y_range = Range1d(y_min, y_max)

    nipy_spectral_colormap = plt.get_cmap("nipy_spectral")
    nipy_spectral_colormap._segmentdata["red"][-1] = (1.0, 0.9, 0.9)
    nipy_spectral_colormap._segmentdata["green"][-1] = (1.0, 0.5, 0.5)
    nipy_spectral_colormap._segmentdata["blue"][-1] = (1.0, 0.5, 0.5)
    nipy_spectral_colormap._init()
    nipy_colors = [
        matplotlib.colors.rgb2hex(plt.get_cmap("nipy_spectral")(i)) for i in range(256)
    ]
    viridis_colors = list(bokeh.palettes.Viridis256)
    custom_color_mapper = bokeh.models.LinearColorMapper(
        palette=nipy_colors + viridis_colors, low=-1.0, high=1.0
    )

    color_arg = {"field": "color", "transform": custom_color_mapper}
    line_color_arg = {"field": "line_color", "transform": custom_color_mapper}

    scatter_scatterplot = points_bokeh_plot.scatter(
        "x",
        "y",
        source=source,
        marker="circle",
        fill_alpha=1.0,
        size="point_size",
        color=color_arg,
        line_color=line_color_arg,
        line_width="line_width",
        line_alpha=1.0,
        name="scatterplot",
    )

    if embedding_size >= 3:
        tooltips = [("coordinates", "[X: @{x_saved}, Y: @{y_saved}, Z: @{z_saved}]")]
    else:
        tooltips = [("coordinates", "[X: @{x_saved}, Y: @{y_saved}]")]
    for elt in tooltip_list:
        tooltips.append((elt, "@{" + elt + "}"))
    hover = HoverTool(tooltips=tooltips)
    points_bokeh_plot.add_tools(hover)
    lasso = LassoSelectTool()
    points_bokeh_plot.add_tools(lasso)
    lasso_select_tool = points_bokeh_plot.select(dict(type=LassoSelectTool))
    lasso_select_tool.continuous = False
    points_bokeh_plot.toolbar.active_drag = points_bokeh_plot.select_one(
        LassoSelectTool
    )
    points_bokeh_plot.toolbar.active_scroll = points_bokeh_plot.select_one(
        WheelZoomTool
    )

    reset = points_bokeh_plot.select(dict(type=ResetTool))
    reset.visible = False
    helpt = points_bokeh_plot.select(dict(type=HelpTool))
    helpt.visible = False

    scatter_scatterplot.nonselection_glyph.fill_alpha = 0.08
    scatter_scatterplot.nonselection_glyph.line_alpha = 0.0
    scatter_scatterplot.nonselection_glyph.fill_color = "gray"

    hover.renderers = [scatter_scatterplot]
    lasso.renderers = [scatter_scatterplot]

    rotmatrix_etc = {
        "0": [1.0, 0.0, 0.0],
        "1": [0.0, 1.0, 0.0],
        "2": [0.0, 0.0, 1.0],
        "delta": [0.0, 0.0, 0.0],
        "center": true_center.flatten().tolist(),
        "offset_angle": [0.0, 0.0, 0.0],
        "max_norm": [xyz_max, -1.0, -1.0],
        "xrange": [x_min, x_max, -1.0],
        "yrange": [y_min, y_max, -1.0],
        "size_coef": [1.0, -1.0, -1.0],
        "width": [
            max(
                points_bokeh_plot.width
                - 41.0,  # 41 is an estimate of the toolbar width
                1.0,
            ),
            -1.0,
            -1.0,
        ],
        "legend_width": [0.0, -1.0, -1.0],
        "height": [
            max(
                points_bokeh_plot.height
                - 31.0,  # 31 is an estimate of the title height
                1.0,
            ),
            -1.0,
            -1.0,
        ],
    }

    source_rotmatrix_etc = bokeh.models.ColumnDataSource(data=rotmatrix_etc)

    tool = CustomAction(
        description="Reset view to selected points",
        icon="reset",
        callback=bokeh.models.CustomJS(
            args=dict(pbp=points_bokeh_plot, source=source),
            code="""
        const indices = source.selected.indices;
        if (indices.length > 0) {
            const subarray_x = indices.map(i => source.data["x"][i]);
            const subarray_y = indices.map(i => source.data["y"][i]);
            pbp.x_range.start = Math.min.apply(null, subarray_x) - 0.00000001;
            pbp.x_range.end = Math.max.apply(null, subarray_x) + 0.00000001;
            pbp.y_range.start = Math.min.apply(null, subarray_y) - 0.00000001;
            pbp.y_range.end = Math.max.apply(null, subarray_y) + 0.00000001;
        } else {
            const subarray_x = source.data["x"];
            const subarray_y = source.data["y"];
            pbp.x_range.start = Math.min.apply(null, subarray_x) - 0.00000001;
            pbp.x_range.end = Math.max.apply(null, subarray_x) + 0.00000001;
            pbp.y_range.start = Math.min.apply(null, subarray_y) - 0.00000001;
            pbp.y_range.end = Math.max.apply(null, subarray_y) + 0.00000001;
        }
    """,
        ),
    )
    points_bokeh_plot.add_tools(tool)

    callback_js_range_change = []

    for elt in [
        "['xrange'][0] = cb_obj.start;",
        "['xrange'][1] = cb_obj.end;",
        "['yrange'][0] = cb_obj.start;",
        "['yrange'][1] = cb_obj.end;",
    ]:
        callback_js_range_change.append(
            bokeh.models.CustomJS(
                args=dict(source_rotmatrix_etc=source_rotmatrix_etc),
                code="""
                const data_rotmatrix_etc = source_rotmatrix_etc.data;
                data_rotmatrix_etc
            """
                + elt,
            )
        )

    points_bokeh_plot.x_range.js_on_change("start", callback_js_range_change[0])
    points_bokeh_plot.x_range.js_on_change("end", callback_js_range_change[1])
    points_bokeh_plot.y_range.js_on_change("start", callback_js_range_change[2])
    points_bokeh_plot.y_range.js_on_change("end", callback_js_range_change[3])

    div_sample_names = bokeh.models.Div(
        width=400, height=50, height_policy="fixed", text="Sample name(s): "
    )
    cb = bokeh.models.CustomJS(
        args=dict(hvr=hover, div=div_sample_names, source=source, col_name="name"),
        code="""
            if (cb_data['index'].indices.length > 0) {
                const data = source.data;
                const line_list = [];
                for (let i = 0; i<cb_data['index'].indices.length; i++) {
                    var line = '<b>"'
                    line += data[col_name][cb_data['index'].indices[i]] + '"</b>'
                    line_list.push(line)
                }
                div.text = "Sample name(s): " + line_list.join(", ");
            }
        """,
    )
    hover.callback = cb  # callback whenever the HoverTool function is called

    callback_js_selected_indices_change = bokeh.models.CustomJS(
        args=dict(
            source=source,
            source_rotmatrix_etc=source_rotmatrix_etc,
            div=div_sample_names,
        ),
        code="""
            const data_rotmatrix_etc = source_rotmatrix_etc.data;
            const rc = data_rotmatrix_etc['center'];
            const data = source.data;
            const x = data['x'];
            const y = data['y'];
            const z = data['z'];
            const indices = source.selected.indices;
            var sum_x = 0.;
            var sum_y = 0.;
            var sum_z = 0.;
            if (indices.length > 0) {
                for (let i = 0; i < indices.length; i++) {
                    sum_x = sum_x + x[indices[i]];
                    sum_y = sum_y + y[indices[i]];
                    sum_z = sum_z + z[indices[i]];
                }
                rc[0] = sum_x / indices.length;
                rc[1] = sum_y / indices.length;
                rc[2] = sum_z / indices.length;
            } else {
                for (let i = 0; i < x.length; i++) {
                    sum_x = sum_x + x[i];
                    sum_y = sum_y + y[i];
                    sum_z = sum_z + z[i];
                }
                rc[0] = sum_x / x.length;
                rc[1] = sum_y / x.length;
                rc[2] = sum_z / x.length;
            }
    """,
    )

    source.selected.js_on_change("indices", callback_js_selected_indices_change)

    stylesheet = InlineStyleSheet(
        css=".noUi-vertical .noUi-origin {top: 0%;} .noUi-base .noUi-connects "
        "{height: 100px;} .noUi-target.noUi-vertical {margin: 10px 0px 0px 25px;}"
    )

    stylesheet2 = InlineStyleSheet(
        css=".noUi-vertical .noUi-origin {top: 0%;} .noUi-base .noUi-connects "
        "{height: "
        + str(height - 55)
        + "px;} .noUi-target.noUi-vertical {margin: 32px 0px 0px -55px;}"
    )

    bt_slider_point_size = bokeh.models.Slider(
        start=0.0,
        end=10.0,
        value=3.0,
        step=0.05,
        title="Point size",
        orientation="vertical",
        stylesheets=[stylesheet],
        width=100,
        show_value=False,
        direction="rtl",
    )

    bt_hidden_slider_yaw = bokeh.models.Slider(
        start=-360.0,
        end=360.0,
        value=0.0,
        step=4.0,
        title="Rotate (yaw)",
        width=100,
        show_value=False,
        name="bt_hidden_slider_yaw",
        visible=False,
    )

    bt_slider_range = bokeh.models.RangeSlider(
        start=0.0,
        end=1.0,
        value=(0.0, 1.0),
        step=0.01,
        orientation="vertical",
        stylesheets=[stylesheet2],
        width=100,
        show_value=False,
        direction="rtl",
        visible=False,
    )

    callback_js_slider_range = bokeh.models.CustomJS(
        args=dict(source=source),
        code="""
        const maxv = cb_obj.end;
        const minv = cb_obj.start;
        const spread = maxv - minv;
        const value_low = (cb_obj.value[0] - minv) / spread;
        const value_high = (cb_obj.value[1] - minv) / spread;
        const data = source.data;
        var t = [];
        const color = data['color'];
        for (let i = 0; i < color.length; i++) {
            if (color[i] >= value_low && color[i] <= value_high) {
                t.push(i);
            }
        }
        source.selected.indices = t;
        source.change.emit();
    """,
    )

    bt_slider_range.js_on_change("value_throttled", callback_js_slider_range)

    bt_toggle_anim = bokeh.models.Toggle(
        label="Animation: OFF", width=100, active=False, name="bt_toggle_anim"
    )

    bt_toggle_anim.js_on_change(
        "active",
        bokeh.models.CustomJS(
            code="""
            if (this.active) {
                this.label = 'Animation: ON';
            } else {
                this.label = 'Animation: OFF';
            }
        """,
        ),
    )

    bt_slider_yaw = bokeh.models.Slider(
        start=-360.0,
        end=360.0,
        value=0.0,
        step=4.0,
        title="Rotate (yaw)",
        width=100,
        show_value=False,
    )

    bt_slider_pitch = bokeh.models.Slider(
        start=-360.0,
        end=360.0,
        value=0.0,
        step=4.0,
        title="Rotate (pitch)",
        orientation="vertical",
        stylesheets=[stylesheet],
        width=100,
        show_value=False,
    )

    bt_slider_roll = bokeh.models.Slider(
        start=-360.0,
        end=360.0,
        value=0.0,
        step=4.0,
        title="Rotate (roll)",
        width=100,
        show_value=False,
    )

    if higher_dim:
        sl_component1 = bokeh.models.RadioButtonGroup(
            labels=["None"] + ["d" + str(i + 1) for i in range(embedding_size)],
            active=1,
            margin=[0, 0, 0, 0],
        )
        sl_component2 = bokeh.models.RadioButtonGroup(
            labels=["None"] + ["d" + str(i + 1) for i in range(embedding_size)],
            active=2,
            margin=[0, 0, 0, 0],
        )
        sl_component3 = bokeh.models.RadioButtonGroup(
            labels=["None"] + ["d" + str(i + 1) for i in range(embedding_size)],
            active=3,
            margin=[0, 0, 0, 0],
        )

    size_redef_code = """
        point_s[i] = point_s_ref[i] * size_coef[0] * (
            2.5 * Math.max(hA[i], hB[i]) + 1.0);
        line_c[i] = -1. + hA[i] * 0.25 + hB[i] * 0.90;
        line_w[i] = point_s_ref[i] * size_coef[0] * 0.85 * Math.max(
            hA[i], hB[i]);
    """

    callback_js_point_size = bokeh.models.CustomJS(
        args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
        code="""
        const f = cb_obj.value;
        const data_rotmatrix_etc = source_rotmatrix_etc.data;
        const size_coef = data_rotmatrix_etc['size_coef'];
        const data = source.data;
        const point_s = data['point_size'];
        const point_s_ref = data['point_size_ref'];
        const hA = data['highlighted_A'];
        const hB = data['highlighted_B'];
        const line_c = data['line_color'];
        const line_w = data['line_width'];
        size_coef[0] = (f/3.)**2;
        for (let i = 0; i < point_s.length; i++) {"""
        + size_redef_code
        + """
        }
        source_rotmatrix_etc.change.emit();
        source.change.emit();
    """,
    )

    bt_slider_point_size.js_on_change("value", callback_js_point_size)

    code_part1_0 = """
        function matrixMultiply(matrix1, matrix2) {
            var result = [];
            var rows1 = matrix1.length;
            var cols1 = matrix1[0].length;
            var rows2 = matrix2.length;
            var cols2 = matrix2[0].length;

            if (cols1 !== rows2) {
                // Matrix multiplication is not possible
                throw new Error("Incompatible matrix dimensions.");
            }

            for (var i = 0; i < rows1; i++) {
                result[i] = [];
                for (var j = 0; j < cols2; j++) {
                    var sum = 0;
                    for (var k = 0; k < cols1; k++) {
                        sum += matrix1[i][k] * matrix2[k][j];
                    }
                    result[i][j] = sum;
                }
            }
            return result;
        }

        function normalize(vec) {
            // Function to normalize a vector
            var norm = Math.sqrt(vec.reduce((acc, val) => acc + val ** 2, 0));
            return vec.map(val => val / norm);
        }

        function rotationMatrix(axis, angle) {
            /**
            * Compute the rotation matrix around a given axis by a given angle.
            *
            * Parameters:
            *     axis: A 3-element array representing the rotation axis.
            *     angle: The rotation angle in radians.
            *
            * Returns:
            *     A 3x3 rotation matrix.
            */
            axis = normalize(axis); // Normalize the axis vector

            var ux = axis[0], uy = axis[1], uz = axis[2];
            var cosTheta = Math.cos(angle);
            var sinTheta = Math.sin(angle);
            var rotMatrix = [
                [
                    cosTheta + ux ** 2 * (1 - cosTheta),
                    ux * uy * (1 - cosTheta) - uz * sinTheta,
                    ux * uz * (1 - cosTheta) + uy * sinTheta
                ],
                [
                    uy * ux * (1 - cosTheta) + uz * sinTheta,
                    cosTheta + uy ** 2 * (1 - cosTheta),
                    uy * uz * (1 - cosTheta) - ux * sinTheta
                ],
                [
                    uz * ux * (1 - cosTheta) - uy * sinTheta,
                    uz * uy * (1 - cosTheta) + ux * sinTheta,
                    cosTheta + uz ** 2 * (1 - cosTheta)
                ]
            ];
            return rotMatrix;
        }

        function scaleTransform(matrix, scale_0, scale_1, scale_2) {
            var matrix1 = [
                [
                    scale_0 /Math.sqrt(scale_1), 0., 0.
                ],
                [
                    0., Math.sqrt(scale_1), 0.
                ],
                [
                    0., 0., scale_2
                ]
            ];
            var matrix2 = [
                [
                     Math.sqrt(scale_1) * 1./scale_0, 0., 0.
                ],
                [
                    0., 1./ Math.sqrt(scale_1), 0.
                ],
                [
                    0., 0., 1./scale_2
                ]
            ];
            return matrixMultiply(matrixMultiply(matrix1, matrix), matrix2)
        }

        function multiplyMatrixVector(matrix, vector) {
            var result = [];
            for (var i = 0; i < matrix.length; i++) {
                var row = matrix[i];
                var sum = 0;
                for (var j = 0; j < row.length; j++) {
                    sum += row[j] * vector[j];
                }
                result.push(sum);
            }
            return result;
        }

        function addVectors(vec1, vec2) {
            var result = [];
            for (var i = 0; i < vec1.length; i++) {
                result.push(vec1[i] + vec2[i]);
            }
            return result;
        }

        function substractVectors(vec1, vec2) {
            var result = [];
            for (var i = 0; i < vec1.length; i++) {
                result.push(vec1[i] - vec2[i]);
            }
            return result;
        }
    """

    code_part1_1 = (
        code_part1_0
        + """
        function argsort(array) {
            // Create an array of indices [0, 1, 2, ..., array.length - 1]
            var indices = Array.from(array.keys());

            // Sort the indices based on the corresponding values in the array
            indices.sort(function(a, b) {
                return array[a] - array[b];
            });

            return indices;
        }

        const data_rotmatrix_etc = source_rotmatrix_etc.data;

        const col0 = data_rotmatrix_etc['0'];
        const col1 = data_rotmatrix_etc['1'];
        const col2 = data_rotmatrix_etc['2'];
        const rdelta = data_rotmatrix_etc['delta'];
        const rc = data_rotmatrix_etc['center'];
        const width = data_rotmatrix_etc[
            'width'][0] - data_rotmatrix_etc['legend_width'][0];
        const height = data_rotmatrix_etc['height'][0];
        const max_norm = data_rotmatrix_etc['max_norm'][0];
        const xr = data_rotmatrix_etc['xrange'];
        const yr = data_rotmatrix_etc['yrange'];
        const size_coef = data_rotmatrix_etc['size_coef'];
        const rmatrix = [col0, col1, col2];
        const data = source.data;
    """
    )

    code_part1_2 = (
        """
        const excludedKeys = ['x', 'y', 'z', 'color', 'x_saved', 'y_saved', 'z_saved',
                              'point_size', 'point_size_ref',
                              'line_color', 'line_width'];
        const other_keys = Object.keys(data).filter(key => !excludedKeys.includes(key));
        const x = data['x'];
        const y = data['y'];
        const z = data['z'];
        const color = data['color'];
        var x_tmp = Array(x.length).fill(0);
        var y_tmp = Array(x.length).fill(0);
        var z_tmp = Array(x.length).fill(0);
        var color_tmp = Array(x.length).fill(0);
        var label_tmp = Array(x.length).fill(0);
        var x_saved_tmp = Array(x.length).fill(0);
        var y_saved_tmp = Array(x.length).fill(0);
        var z_saved_tmp = Array(x.length).fill(0);
        const x_saved = data['x_saved'];
        const y_saved = data['y_saved'];
        const z_saved = data['z_saved'];
        const point_s = data['point_size'];
        const point_s_ref = data['point_size_ref'];
        const hA = data['highlighted_A'];
        const hB = data['highlighted_B'];
        const line_c = data['line_color'];
        const line_w = data['line_width'];
        var pst = Array(x.length).fill(0);
        var other_keys_array_tmp = Array.from(
            { length: other_keys.length }, () => Array(x.length).fill(0));
        const scaleCoef = (
            yr[1]-yr[0] + 0.00000001)/(xr[1]-xr[0] + 0.00000001) * width/height;
        const rotmataxis = scaleTransform(
            rotationMatrix(rotaxis, f * Math.PI/180.0), 1., scaleCoef, 1.);
        const rot_m = matrixMultiply(rotmataxis, rmatrix);
        const delta_vec = addVectors(
            rc, multiplyMatrixVector(rotmataxis, substractVectors(rdelta, rc)));
        var rot_result = [0, 0, 0];
        """
        + (
            """
        const dim1 = 'original_embedding_' + (slc1.active - 1).toString();
        const dimif1 = (slc1.active > 0);
        const dim2 = 'original_embedding_' + (slc2.active - 1).toString();
        const dimif2 = (slc2.active > 0);
        const dim3 = 'original_embedding_' + (slc3.active - 1).toString();
        const dimif3 = (slc3.active > 0);
        """
            if higher_dim
            else ""
        )
        + """
        for (let i = 0; i < x.length; i++) {
            """
        + (
            """
            x_saved[i] = 0.;
            y_saved[i] = 0.;
            z_saved[i] = 0.;
            if (dimif1) {
                x_saved[i] += data[dim1][i];
            }
            if (dimif2) {
                y_saved[i] += data[dim2][i];
            }
            if (dimif3) {
                z_saved[i] += data[dim3][i];
            }
            """
            if higher_dim
            else ""
        )
        + """
            rot_result = multiplyMatrixVector(
                rot_m, [x_saved[i], y_saved[i], z_saved[i]]);
            x_tmp[i] = rot_result[0] + delta_vec[0];
            y_tmp[i] = rot_result[1] + delta_vec[1];
            z_tmp[i] = rot_result[2] + delta_vec[2];
            color_tmp[i] = color[i];
            x_saved_tmp[i] = x_saved[i];
            y_saved_tmp[i] = y_saved[i];
            z_saved_tmp[i] = z_saved[i];
            pst[i] = 5. / (1. + Math.exp(Math.min(Math.max(
                (-z_tmp[i] + rc[2])/ (max_norm + 0.0000001), -1.), 1.)));
            for (let j = 0; j < other_keys.length; j++) {
                other_keys_array_tmp[j][i] = data[other_keys[j]][i]
            }
        }
        var new_order = argsort(z_tmp);
        var transform_indices = Array(x.length).fill(0);
        for (let i = 0; i < x.length; i++) {
            var k = new_order[i];
            transform_indices[k] = i;
            x[i] = x_tmp[k];
            y[i] = y_tmp[k];
            z[i] = z_tmp[k];
            color[i] = color_tmp[k];
            x_saved[i] = x_saved_tmp[k];
            y_saved[i] = y_saved_tmp[k];
            z_saved[i] = z_saved_tmp[k];
            point_s_ref[i] = pst[k];
            for (let j = 0; j < other_keys.length; j++) {
                data[other_keys[j]][i] = other_keys_array_tmp[j][k]
            }"""
        + size_redef_code
        + """
        }

        const indices = source.selected.indices
        for (let i = 0; i < indices.length; i++) {
            indices[i] = transform_indices[indices[i]]
        }

        source_rotmatrix_etc.change.emit();
        source.change.emit();
    """
    )

    code_part2_1 = (
        code_part1_0
        + """
        const data_rotmatrix_etc = source_rotmatrix_etc.data;

        const col0 = data_rotmatrix_etc['0'];
        const col1 = data_rotmatrix_etc['1'];
        const col2 = data_rotmatrix_etc['2'];
        const rdelta = data_rotmatrix_etc['delta'];
        const rc = data_rotmatrix_etc['center'];
        const width = data_rotmatrix_etc[
            'width'][0] - data_rotmatrix_etc['legend_width'][0];
        const height = data_rotmatrix_etc['height'][0];
        const xr = data_rotmatrix_etc['xrange'];
        const yr = data_rotmatrix_etc['yrange'];
        const offset = data_rotmatrix_etc['offset_angle'];
        const rmatrix = [col0, col1, col2];
    """
    )

    code_part2_2 = """
        const scaleCoef = (
            yr[1]-yr[0] + 0.00000001)/(xr[1]-xr[0] + 0.00000001) * width/height;
        const rotmataxis = scaleTransform(
            rotationMatrix(rotaxis, f * Math.PI/180.0), 1., scaleCoef, 1.);
        const rot_m = matrixMultiply(rotmataxis, rmatrix);
        const delta_vec = addVectors(
            rc, multiplyMatrixVector(rotmataxis, substractVectors(rdelta, rc)));

        col0[0] = rot_m[0][0];
        col0[1] = rot_m[0][1];
        col0[2] = rot_m[0][2];
        col1[0] = rot_m[1][0];
        col1[1] = rot_m[1][1];
        col1[2] = rot_m[1][2];
        col2[0] = rot_m[2][0];
        col2[1] = rot_m[2][1];
        col2[2] = rot_m[2][2];

        rdelta[0] = delta_vec[0];
        rdelta[1] = delta_vec[1];
        rdelta[2] = delta_vec[2];

    """

    reset_slider_yaw = (
        """
            if (bsy.value != 0) {
        """
        + code_part2_1
        + """
            const offset_x = offset[0];
            const f = bsy.value - offset_x;
            const rotaxis = [0, 1, 0];
        """
        + code_part2_2
        + """
            offset[0] = 0;
            source_rotmatrix_etc.change.emit();
            bsy.value = 0;
            bsy.change.emit();
            }
    """
    )
    reset_slider_pitch = (
        """
            if (bsp.value != 0) {
        """
        + code_part2_1
        + """
            const offset_y = offset[1];
            const f = bsp.value - offset_y;
            const rotaxis = [1, 0, 0];
        """
        + code_part2_2
        + """
            offset[1] = 0;
            source_rotmatrix_etc.change.emit();
            bsp.value = 0;
            bsp.change.emit();
            }
    """
    )
    reset_slider_roll = (
        """
            if (bsr.value != 0) {
        """
        + code_part2_1
        + """
            const offset_z = offset[2];
            const f = bsr.value - offset_z;
            const rotaxis = [0, 0, 1];
        """
        + code_part2_2
        + """
            offset[2] = 0;
            source_rotmatrix_etc.change.emit();
            bsr.value = 0;
            bsr.change.emit();
            }
    """
    )

    if higher_dim:
        callback_js2 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                slc1=sl_component1,
                slc2=sl_component2,
                slc3=sl_component3,
                bsp=bt_slider_pitch,
                bsr=bt_slider_roll,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_pitch
            + reset_slider_roll
            + code_part1_1
            + """
                const offset_x = data_rotmatrix_etc['offset_angle'][0];
                const f = cb_obj.value - offset_x;
                const rotaxis = [0, 1, 0];
            """
            + code_part1_2,
        )
    else:
        callback_js2 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                bsp=bt_slider_pitch,
                bsr=bt_slider_roll,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_pitch
            + reset_slider_roll
            + code_part1_1
            + """
                const offset_x = data_rotmatrix_etc['offset_angle'][0];
                const f = cb_obj.value - offset_x;
                const rotaxis = [0, 1, 0];
            """
            + code_part1_2,
        )

    callback_js3 = bokeh.models.CustomJS(
        args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
        code=code_part2_1
        + """
            const offset_x = offset[0];
            const f = cb_obj.value - offset_x;
            const rotaxis = [0, 1, 0];
        """
        + code_part2_2
        + """
            offset[0] = 0;
            source_rotmatrix_etc.change.emit();
            cb_obj.value = 0;
            cb_obj.change.emit();
        """,
    )

    code_full = """
        const new_offset = data_rotmatrix_etc['offset_angle'];
        const new_offset_x = new_offset[0];
        const new_f = cb_obj.value - new_offset_x;
        const new_rotaxis = [0, 1, 0];
        const new_scaleCoef = (
            yr[1]-yr[0] + 0.00000001)/(xr[1]-xr[0] + 0.00000001) * width/height;
        const new_rotmataxis = scaleTransform(
            rotationMatrix(new_rotaxis, new_f * Math.PI/180.0), 1., new_scaleCoef, 1.);
        const new_rot_m = matrixMultiply(new_rotmataxis, rmatrix);
        const new_delta_vec = addVectors(
            rc, multiplyMatrixVector(new_rotmataxis, substractVectors(rdelta, rc)));

        col0[0] = new_rot_m[0][0];
        col0[1] = new_rot_m[0][1];
        col0[2] = new_rot_m[0][2];
        col1[0] = new_rot_m[1][0];
        col1[1] = new_rot_m[1][1];
        col1[2] = new_rot_m[1][2];
        col2[0] = new_rot_m[2][0];
        col2[1] = new_rot_m[2][1];
        col2[2] = new_rot_m[2][2];

        rdelta[0] = new_delta_vec[0];
        rdelta[1] = new_delta_vec[1];
        rdelta[2] = new_delta_vec[2];
        new_offset[0] = 0;
        source_rotmatrix_etc.change.emit();
        cb_obj.value = 0;
        cb_obj.change.emit();
    """

    if higher_dim:
        callback_full = bokeh.models.CustomJS(
            args=dict(
                slc1=sl_component1,
                slc2=sl_component2,
                slc3=sl_component3,
                bsp=bt_slider_pitch,
                bsr=bt_slider_roll,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code=reset_slider_pitch
            + reset_slider_roll
            + code_part1_1
            + """
                const offset_x = data_rotmatrix_etc['offset_angle'][0];
                const f = cb_obj.value - offset_x;
                const rotaxis = [0, 1, 0];
            """
            + code_part1_2
            + code_full,
        )
    else:
        callback_full = bokeh.models.CustomJS(
            args=dict(
                bsp=bt_slider_pitch,
                bsr=bt_slider_roll,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code=reset_slider_pitch
            + reset_slider_roll
            + code_part1_1
            + """
                const offset_x = data_rotmatrix_etc['offset_angle'][0];
                const f = cb_obj.value - offset_x;
                const rotaxis = [0, 1, 0];
            """
            + code_part1_2
            + code_full,
        )

    bt_slider_yaw.js_on_change("value", callback_js2)
    bt_slider_yaw.js_on_change("value_throttled", callback_js3)

    bt_hidden_slider_yaw.js_on_change("value", callback_full)

    if higher_dim:
        callback_js4 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                slc1=sl_component1,
                slc2=sl_component2,
                slc3=sl_component3,
                bsr=bt_slider_roll,
                bsy=bt_slider_yaw,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_roll
            + reset_slider_yaw
            + code_part1_1
            + """
                const offset_y = data_rotmatrix_etc['offset_angle'][1];
                const f = cb_obj.value - offset_y;
                const rotaxis = [1, 0, 0];
            """
            + code_part1_2,
        )
    else:
        callback_js4 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                bsr=bt_slider_roll,
                bsy=bt_slider_yaw,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_roll
            + reset_slider_yaw
            + code_part1_1
            + """
                const offset_y = data_rotmatrix_etc['offset_angle'][1];
                const f = cb_obj.value - offset_y;
                const rotaxis = [1, 0, 0];
            """
            + code_part1_2,
        )

    callback_js5 = bokeh.models.CustomJS(
        args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
        code=code_part2_1
        + """
            const offset_y = offset[1];
            const f = cb_obj.value - offset_y;
            const rotaxis = [1, 0, 0];
        """
        + code_part2_2
        + """
            offset[1] = 0;
            source_rotmatrix_etc.change.emit();
            cb_obj.value = 0;
            cb_obj.change.emit();
        """,
    )

    bt_slider_pitch.js_on_change("value", callback_js4)
    bt_slider_pitch.js_on_change("value_throttled", callback_js5)

    if higher_dim:
        callback_js6 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                slc1=sl_component1,
                slc2=sl_component2,
                slc3=sl_component3,
                bsp=bt_slider_pitch,
                bsy=bt_slider_yaw,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_pitch
            + reset_slider_yaw
            + code_part1_1
            + """
                const offset_z = data_rotmatrix_etc['offset_angle'][2];
                const f = cb_obj.value - offset_z;
                const rotaxis = [0, 0, 1];
            """
            + code_part1_2,
        )
    else:
        callback_js6 = bokeh.models.CustomJS(
            args=dict(
                bta=bt_toggle_anim,
                bsp=bt_slider_pitch,
                bsy=bt_slider_yaw,
                source=source,
                source_rotmatrix_etc=source_rotmatrix_etc,
            ),
            code="""bta.active = false;"""
            + reset_slider_pitch
            + reset_slider_yaw
            + code_part1_1
            + """
                const offset_z = data_rotmatrix_etc['offset_angle'][2];
                const f = cb_obj.value - offset_z;
                const rotaxis = [0, 0, 1];
            """
            + code_part1_2,
        )

    callback_js7 = bokeh.models.CustomJS(
        args=dict(source=source, source_rotmatrix_etc=source_rotmatrix_etc),
        code=code_part2_1
        + """
            const offset_z = offset[2];
            const f = cb_obj.value - offset_z;
            const rotaxis = [0, 0, 1];
        """
        + code_part2_2
        + """
            offset[2] = 0;
            source_rotmatrix_etc.change.emit();
            cb_obj.value = 0;
            cb_obj.change.emit();
        """,
    )

    bt_slider_roll.js_on_change("value", callback_js6)
    bt_slider_roll.js_on_change("value_throttled", callback_js7)

    if higher_dim:
        slc_data = {
            "1": [sl_component1.active],
            "2": [sl_component2.active],
            "3": [sl_component3.active],
        }
        slc_source = bokeh.models.ColumnDataSource(data=slc_data)

        code_callback_slc = (
            code_part1_1
            + """
            const excludedKeys = ['x', 'y', 'z', 'color', 'x_saved', 'y_saved',
                                'z_saved', 'point_size', 'point_size_ref',
                                'line_color', 'line_width'];
            const other_keys = Object.keys(data).filter(
                key => !excludedKeys.includes(key));
            const x = data['x'];
            const y = data['y'];
            const z = data['z'];
            const color = data['color'];
            var x_tmp = Array(x.length).fill(0);
            var y_tmp = Array(x.length).fill(0);
            var z_tmp = Array(x.length).fill(0);
            var color_tmp = Array(x.length).fill(0);
            var label_tmp = Array(x.length).fill(0);
            var x_saved_tmp = Array(x.length).fill(0);
            var y_saved_tmp = Array(x.length).fill(0);
            var z_saved_tmp = Array(x.length).fill(0);
            const x_saved = data['x_saved'];
            const y_saved = data['y_saved'];
            const z_saved = data['z_saved'];
            const point_s = data['point_size'];
            const point_s_ref = data['point_size_ref'];
            const hA = data['highlighted_A'];
            const hB = data['highlighted_B'];
            const line_c = data['line_color'];
            const line_w = data['line_width'];
            var pst = Array(x.length).fill(0);
            var other_keys_array_tmp = Array.from(
                { length: other_keys.length }, () => Array(x.length).fill(0));
            const rot_m = rmatrix;
            const delta_vec = rdelta;
            var rot_result = [0, 0, 0];
            const dim1 = 'original_embedding_' + (cb_obj.data['1'] - 1).toString();
            const dimif1 = (cb_obj.data['1'] > 0);
            const dim2 = 'original_embedding_' + (cb_obj.data['2'] - 1).toString();
            const dimif2 = (cb_obj.data['2'] > 0);
            const dim3 = 'original_embedding_' + (cb_obj.data['3'] - 1).toString();
            const dimif3 = (cb_obj.data['3'] > 0);
            for (let i = 0; i < x.length; i++) {
                x_saved[i] = 0.;
                y_saved[i] = 0.;
                z_saved[i] = 0.;
                if (dimif1) {
                    x_saved[i] += data[dim1][i];
                }
                if (dimif2) {
                    y_saved[i] += data[dim2][i];
                }
                if (dimif3) {
                    z_saved[i] += data[dim3][i];
                }
                rot_result = multiplyMatrixVector(
                    rot_m, [x_saved[i], y_saved[i], z_saved[i]]);
                x_tmp[i] = rot_result[0] + delta_vec[0];
                y_tmp[i] = rot_result[1] + delta_vec[1];
                z_tmp[i] = rot_result[2] + delta_vec[2];
                color_tmp[i] = color[i];
                x_saved_tmp[i] = x_saved[i];
                y_saved_tmp[i] = y_saved[i];
                z_saved_tmp[i] = z_saved[i];
                pst[i] = 5. / (1. + Math.exp(Math.min(Math.max(
                    (-z_tmp[i] + rc[2])/ (max_norm + 0.0000001), -1.), 1.)));
                for (let j = 0; j < other_keys.length; j++) {
                    other_keys_array_tmp[j][i] = data[other_keys[j]][i]
                }
            }
            var new_order = argsort(z_tmp);
            var transform_indices = Array(x.length).fill(0);
            for (let i = 0; i < x.length; i++) {
                var k = new_order[i];
                transform_indices[k] = i;
                x[i] = x_tmp[k];
                y[i] = y_tmp[k];
                z[i] = z_tmp[k];
                color[i] = color_tmp[k];
                x_saved[i] = x_saved_tmp[k];
                y_saved[i] = y_saved_tmp[k];
                z_saved[i] = z_saved_tmp[k];
                point_s_ref[i] = pst[k];
                for (let j = 0; j < other_keys.length; j++) {
                    data[other_keys[j]][i] = other_keys_array_tmp[j][k]
                }"""
            + size_redef_code
            + """
            }
            const indices = source.selected.indices
            for (let i = 0; i < indices.length; i++) {
                indices[i] = transform_indices[indices[i]]
            }
            var sum_x = 0.;
            var sum_y = 0.;
            var sum_z = 0.;
            if (indices.length > 0) {
                for (let i = 0; i < indices.length; i++) {
                    sum_x = sum_x + x[indices[i]];
                    sum_y = sum_y + y[indices[i]];
                    sum_z = sum_z + z[indices[i]];
                }
                rc[0] = sum_x / indices.length;
                rc[1] = sum_y / indices.length;
                rc[2] = sum_z / indices.length;
            } else {
                for (let i = 0; i < x.length; i++) {
                    sum_x = sum_x + x[i];
                    sum_y = sum_y + y[i];
                    sum_z = sum_z + z[i];
                }
                rc[0] = sum_x / x.length;
                rc[1] = sum_y / x.length;
                rc[2] = sum_z / x.length;
            }
            source_rotmatrix_etc.change.emit();
            source.change.emit();
        """
        )

        sl_component1.js_on_change(
            "active",
            bokeh.models.CustomJS(
                args=dict(
                    slcs=slc_source,
                ),
                code="""
                    // Full copy to trigger the change callback
                    var t = {};
                    for (const key in slcs.data) {
                        t[key] = [];
                        t[key].push(slcs.data[key][0]);
                    }
                    t['1'][0] = cb_obj.active;
                    slcs.data = t;
                    slcs.change.emit();
                """,
            ),
        )
        sl_component2.js_on_change(
            "active",
            bokeh.models.CustomJS(
                args=dict(
                    slcs=slc_source,
                ),
                code="""
                    // Full copy to trigger the change callback
                    var t = {};
                    for (const key in slcs.data) {
                        t[key] = [];
                        t[key].push(slcs.data[key][0]);
                    }
                    t['2'][0] = cb_obj.active;
                    slcs.data = t;
                    slcs.change.emit();
                """,
            ),
        )
        sl_component3.js_on_change(
            "active",
            bokeh.models.CustomJS(
                args=dict(
                    slcs=slc_source,
                ),
                code="""
                    // Full copy to trigger the change callback
                    var t = {};
                    for (const key in slcs.data) {
                        t[key] = [];
                        t[key].push(slcs.data[key][0]);
                    }
                    t['3'][0] = cb_obj.active;
                    slcs.data = t;
                    slcs.change.emit();
                """,
            ),
        )

        slc_source.js_on_change(
            "data",
            bokeh.models.CustomJS(
                args=dict(
                    source=source,
                    source_rotmatrix_etc=source_rotmatrix_etc,
                ),
                code=code_callback_slc,
            ),
        )

    resize_width_input = bokeh.models.TextInput(
        value=str(points_bokeh_plot.width),
        title="Width:",
        name="resize_width",
        width=54,
        margin=(5, 0, 5, 0),
    )
    resize_width_input.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(pbp=points_bokeh_plot, source_rotmatrix_etc=source_rotmatrix_etc),
            code="""
        var parsed_int = parseInt(this.value);
        if (!isNaN(parsed_int)) {
            pbp.width = parsed_int;
            source_rotmatrix_etc.data['width'][0] = Math.max(parsed_int - 41., 1.);
            source_rotmatrix_etc.change.emit();
            pbp.change.emit();
        }
    """,
        ),
    )

    resize_height_input = bokeh.models.TextInput(
        value=str(points_bokeh_plot.height),
        title="Height:",
        name="resize_height",
        width=54,
        margin=(5, 0, 5, 0),
    )
    resize_height_input.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(
                pbp=points_bokeh_plot,
                source_rotmatrix_etc=source_rotmatrix_etc,
                slider_range=bt_slider_range,
            ),
            code="""
        var parsed_int = parseInt(this.value);
        if (!isNaN(parsed_int)) {
            pbp.height = parsed_int;
            source_rotmatrix_etc.data['height'][0] = Math.max(parsed_int - 31., 1.);
            source_rotmatrix_etc.change.emit();
            pbp.change.emit();
            //slider_range.value = [ 0.0, 1.0 ];
            //slider_range.change.emit();
        }
    """,
        ),
    )

    def modif_slider_range(attr, old, new):
        current_style = bt_slider_range.stylesheets[0].css
        pattern = r"\{height: \d+px;\}"
        new_style = re.sub(
            pattern, "{height: " + str(max(int(new) - 55, 0)) + "px;}", current_style
        )
        bt_slider_range.stylesheets = [InlineStyleSheet(css=new_style)]

    resize_height_input.on_change(
        "value", lambda attr, old, new: modif_slider_range(attr, old, new)
    )

    sample_search_input = bokeh.models.TextInput(
        value="",
        title="Sample search (enter sample name):",
        name="sample_search_input",
        width=650,
    )

    sample_search_input.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(source=source),
            code="""
        const data = source.data;
        for (let i=0; i<data["name"].length; i++) {
            if (data["name"][i] == this.value) {
                source.selected.indices = new Array(1).fill(i);
            }
        }
    """,
        ),
    )

    def copy_figure(original, title):
        new_fig = bkp.figure(
            title=title,
            x_axis_label=original.xaxis.axis_label,
            y_axis_label=original.yaxis.axis_label,
        )

        new_fig.width = original.width
        new_fig.height = original.height
        new_fig.background_fill_color = original.background_fill_color
        new_fig.border_fill_color = original.border_fill_color
        new_fig.toolbar_location = "left"
        return new_fig

    violin_plot = copy_figure(points_bokeh_plot, "Violin plots")
    violin_plot.visible = False
    heatmap_plot = copy_figure(points_bokeh_plot, "Heatmap")
    heatmap_plot.visible = False

    resize_width_input_bis = bokeh.models.TextInput(
        value=str(points_bokeh_plot.width),
        title="Width:",
        name="resize_width_bis",
        width=54,
        margin=(5, 0, 5, 0),
    )
    resize_width_input_bis.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(vp=violin_plot, hp=heatmap_plot),
            code="""
        var parsed_int = parseInt(this.value);
        if (!isNaN(parsed_int)) {
            vp.width = parsed_int;
            hp.width = parsed_int;
            vp.change.emit();
            hp.change.emit();
        }
    """,
        ),
    )

    resize_height_input_bis = bokeh.models.TextInput(
        value=str(points_bokeh_plot.height),
        title="Height:",
        name="resize_height_bis",
        width=54,
        margin=(5, 0, 5, 0),
    )
    resize_height_input_bis.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(vp=violin_plot, hp=heatmap_plot),
            code="""
        var parsed_int = parseInt(this.value);
        if (!isNaN(parsed_int)) {
            vp.height = parsed_int;
            hp.height = parsed_int;
            vp.change.emit();
            hp.change.emit();
        }
    """,
        ),
    )

    if higher_dim:
        return (
            obs_string,
            obs_numerical,
            points_bokeh_plot,
            violin_plot,
            heatmap_plot,
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
        )
    else:
        return (
            obs_string,
            obs_numerical,
            points_bokeh_plot,
            violin_plot,
            heatmap_plot,
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
            None,
            None,
            None,
        )
