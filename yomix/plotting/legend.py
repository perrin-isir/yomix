import bokeh.models
import numpy as np
from pathlib import Path
from PIL import ImageFont
import re
from bokeh.models import InlineStyleSheet


def setup_legend(
    pb_plot,
    obs_string,
    obs_numerical,
    source_rotmatrix_etc,
    resize_width_input,
    bt_slider_range,
):
    source = pb_plot.select(dict(name="scatterplot"))[0].data_source

    hidden_text_label_column = bokeh.models.TextInput(
        value="", title="Label column", name="hidden_text_label_column", width=999
    )
    hidden_text_label_column.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(source=source, obss=obs_string, obsn=obs_numerical),
            code="""
        if (obss.includes(this.value)) {
            const data = source.data;
            function onlyUnique(value, index, array) {
                return array.indexOf(value) === index;
            }
            var unique = data[this.value].filter(onlyUnique);
            unique.sort();
            var l_values = new Array(unique.length).fill(0);
            const step = 1./(Math.max(unique.length - 1, 1)) * 0.999999;
            var l_values_dict = {};
            l_values_dict[unique[0]] = -1.;
            for (let i = 1; i < l_values.length; i++) {
                l_values[i] = l_values[i-1] + step;
                l_values_dict[unique[i]] = l_values[i]-1.;
            }
            for (let i = 0; i < data["color"].length; i++) {
                data["color"][i] = l_values_dict[data[this.value][i]];
            }
            source.change.emit();
        }
        if (obsn.includes(this.value)) {
            const data = source.data;
            var max_val = Math.max(...data[this.value]);
            var min_val = Math.min(...data[this.value]);
            for (let i = 0; i < data["color"].length; i++) {
                data["color"][i] = (data[this.value][i] - min_val) / (
                    max_val - min_val + 0.000001);
            }
            source.change.emit();
        }
    """,
        ),
    )
    hidden_text_label_column_bis = bokeh.models.TextInput(
        value="",
        title="Label column bis",
        name="hidden_text_label_column_bis",
        width=999,
    )

    hidden_legend_width = bokeh.models.TextInput(
        value="0", title="Legend width", name="hidden_legend_width", width=999
    )
    hidden_legend_width.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(source_rotmatrix_etc=source_rotmatrix_etc),
            code="""
        var parsed_int = parseInt(this.value);
        if (!isNaN(parsed_int)) {
            source_rotmatrix_etc.data['legend_width'][0] = parsed_int * 1.;
            source_rotmatrix_etc.change.emit();
        }
    """,
        ),
    )

    def redefine_custom_legend(
        bokeh_plot,
        htls,
        htlc,
        htlcbis,
        hlw,
        obs_col,
        legend_dict,
        rwi,
        obs_s,
        obs_n,
        bt_slider_range,
    ):
        if obs_col in obs_s:
            bokeh_plot.right = []
            htlc.value = obs_col
            htlcbis.value = obs_col
            if obs_col in legend_dict:
                legend_list = legend_dict[obs_col][0]
                for legend in legend_list:
                    bokeh_plot.add_layout(legend, "right")
                rwi.value = str(
                    int(bokeh_plot.width - float(hlw.value) + legend_dict[obs_col][1])
                )
                hlw.value = str(legend_dict[obs_col][1])
            else:

                def all_values(arr) -> np.ndarray:
                    av = np.array(list(dict.fromkeys(arr)))
                    av.sort()
                    return av

                data = bokeh_plot.select(dict(name="scatterplot"))[0].data_source.data
                list_vals = all_values(data[obs_col])

                if len(list_vals) == 1:
                    l_values = [0.0]
                else:
                    l_values = (
                        np.arange(0, 1.0000001, 1.0 / (len(list_vals) - 1)) * 0.999999
                    )
                glyph = bokeh_plot.select(dict(name="scatterplot"))[0].glyph
                palette = glyph.fill_color["transform"].palette[0:256]
                l_colors = [palette[int(256 * val)] for val in l_values]
                height = 24
                margin = 0
                spacing = 0
                padding = 5
                max_nr = (bokeh_plot.height - 2 * margin - 2 * padding - height) // (
                    height + spacing
                )
                full_length = len(list_vals)
                cuts = list(np.arange(0, full_length, max_nr)) + [full_length]
                list_intervals = [
                    np.arange(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)
                ]
                legend_list = [bokeh.models.Legend(items=[], visible=False, name="0")]
                bokeh_plot.add_layout(legend_list[0], "right")
                legend_width = 0

                scatter_circles = [
                    bokeh_plot.add_glyph(
                        bokeh.models.Scatter(
                            size=0, x=0, y=0, line_width=0, fill_color=l_colors[i]
                        )
                    )
                    for i in range(full_length)
                ]

                iteration = 0
                for itvl in list_intervals:
                    iteration += 1
                    items_list = [
                        (
                            list_vals[i],
                            [scatter_circles[i]],
                        )
                        for i in itvl
                    ]
                    legend = bokeh.models.Legend(
                        items=items_list,
                        label_height=height,
                        glyph_height=height,
                        spacing=spacing,
                        padding=padding,
                        margin=margin,
                    )
                    legend.click_policy = "mute"
                    for i in range(len(legend.items)):
                        cb_js = bokeh.models.CustomJS(
                            args=dict(
                                htls=htls,
                                label=legend.items[i].label.value,
                                renderer=legend.items[i].renderers[0],
                            ),
                            code="""
                                if (!renderer.muted) {
                                    htls.value = label;
                                }
                                else {
                                    htls.value = "";
                                }
                                renderer.muted = false;
                            """,
                        )
                        legend.items[i].renderers[0].js_on_change("change:muted", cb_js)
                    legend.label_text_font = "Helvetica"
                    if iteration == 1:
                        label_font_size = legend.label_text_font_size
                        # It's a string like '13px' so need to int-ify it:
                        label_font_size = int(label_font_size[:-2])
                        font = ImageFont.truetype(
                            (Path(__file__).parent.parent / "assets" / "helvetica.ttf")
                            .absolute()
                            .as_posix(),
                            label_font_size,
                        )
                    all_label_width = [
                        font.getlength(x.label["value"]) for x in legend.items
                    ]
                    max_label_width = max(all_label_width)
                    width_increment = (
                        legend.border_line_width
                        + legend.glyph_width
                        + max_label_width
                        + 14
                    )
                    legend_width += width_increment
                    legend.name = str(width_increment)
                    bokeh_plot.add_layout(legend, "right")
                    legend_list.append(legend)
                rwi.value = str(int(bokeh_plot.width - float(hlw.value) + legend_width))
                hlw.value = str(int(legend_width))
                legend_dict[obs_col] = (legend_list, legend_width)
        bt_slider_range.visible = False
        if obs_col in obs_n:
            if bokeh_plot.right:
                decrement = float(bokeh_plot.right[0].name)
                bokeh_plot.right.pop(0)
            else:
                decrement = 0.0
            htlc.value = obs_col
            if obs_col in legend_dict:
                legend_list = legend_dict[obs_col][0]
                legend_len = len(bokeh_plot.right)
                cbar = legend_list[0]
                bokeh_plot.right = [cbar] + bokeh_plot.right
                min_val = cbar.ticker.ticks[0]
                max_val = cbar.ticker.ticks[-1]
                if legend_len > 0:
                    legend_width_modif = (
                        legend_dict[obs_col][1] + float(hlw.value) - decrement
                    )
                else:
                    legend_width_modif = legend_dict[obs_col][1]
                rwi.value = str(
                    int(bokeh_plot.width - float(hlw.value) + legend_width_modif)
                )
                hlw.value = str(legend_width_modif)
            else:
                data = bokeh_plot.select(dict(name="scatterplot"))[0].data_source.data
                max_val = data[obs_col].max()
                min_val = data[obs_col].min()
                viridis_colors = list(bokeh.palettes.Viridis256)
                custom_color_mapper = bokeh.models.LinearColorMapper(
                    palette=viridis_colors, low=min_val, high=max_val
                )
                ltick_vals = [
                    min_val,
                    (max_val + 3.0 * min_val) / 4.0,
                    (max_val + min_val) / 2.0,
                    (3.0 * max_val + min_val) / 4.0,
                    max_val,
                ]
                cbar = bokeh.models.ColorBar(
                    color_mapper=custom_color_mapper,
                    label_standoff=12,
                    width=47,
                    ticker=bokeh.models.FixedTicker(ticks=ltick_vals),
                )
                cbar.major_label_overrides = {
                    nbr: f"""{float(f"{nbr:.3E}"):.10f}""".rstrip("0") + "0"
                    for nbr in ltick_vals
                }
                legend_len = len(bokeh_plot.right)
                bokeh_plot.right = [cbar] + bokeh_plot.right
                tick_strings = list(cbar.major_label_overrides.values())
                label_font_size = cbar.major_label_text_font_size
                label_font_size = int(label_font_size[:-2])
                font = ImageFont.truetype(
                    (Path(__file__).parent.parent / "assets" / "helvetica.ttf")
                    .absolute()
                    .as_posix(),
                    label_font_size,
                )
                all_tick_width = [font.getlength(x) for x in tick_strings]
                max_tick_width = max(all_tick_width)
                legend_width = 30 + cbar.width + max_tick_width
                cbar.name = str(legend_width)
                if legend_len > 0:
                    legend_width_modif = legend_width + float(hlw.value) - decrement
                else:
                    legend_width_modif = legend_width
                rwi.value = str(
                    int(bokeh_plot.width - float(hlw.value) + legend_width_modif)
                )
                hlw.value = str(int(legend_width_modif))
                legend_dict[obs_col] = ([cbar], legend_width)
            current_style = bt_slider_range.stylesheets[0].css
            pattern = r"\{margin: 32px 0px 0px -\d+px;\}"
            new_style = re.sub(
                pattern,
                "{margin: 32px 0px 0px -" + str(int(legend_width_modif - 13)) + "px;}",
                current_style,
            )
            bt_slider_range.stylesheets = [InlineStyleSheet(css=new_style)]
            bt_slider_range.start = min_val
            bt_slider_range.end = max_val
            bt_slider_range.value = (min_val, max_val)
            bt_slider_range.step = (max_val - min_val) / 100.0
            bt_slider_range.visible = True

    hidden_text_label_search = bokeh.models.TextInput(
        value="", title="Label search", name="hidden_text_label_search", width=999
    )

    legend_dict = {}

    modifiers_data = {"shift": [0]}

    source_modifiers = bokeh.models.ColumnDataSource(data=modifiers_data)

    pb_plot.js_on_event(
        bokeh.events.Tap,
        bokeh.models.CustomJS(
            args=dict(
                source_modif=source_modifiers,
                htls=hidden_text_label_search,
            ),
            code="""
        const smd = source_modif.data;
        if (cb_obj.modifiers.shift) {
            smd["shift"][0] = 1;
        } else {
            smd["shift"][0] = 0;
        }
        source_modif.change.emit();
    """,
        ),
    )

    hidden_text_label_search.js_on_change(
        "value",
        bokeh.models.CustomJS(
            args=dict(
                source=source,
                source_modif=source_modifiers,
                htlc=hidden_text_label_column,
                htlc_bis=hidden_text_label_column_bis,
                hlw=hidden_legend_width,
            ),
            code="""
        const smd = source_modif.data;
        const data = source.data;
        const labels = data[htlc_bis.value];
        if (smd["shift"][0] == 1) {
            if (this.value.slice(-25, this.value.length) != "[-.-.-.-.-shift-.-.-.-.-]")
            {
                const val = this.value;
                this.value = val + "[-.-.-.-.-shift-.-.-.-.-]";
                const indices = source.selected.indices;
                for (let i = 0; i < indices.length; i++) {
                    if (labels[indices[i]] == val) {
                        indices.splice(i, 1);
                    }
                }
                for (let i = 0; i < labels.length; i++) {
                    if (labels[i] == val) {
                        indices.push(i);
                    }
                }
                source.change.emit();
            }
        } else {
            if (this.value.slice(-25, this.value.length) != "[-.-.-.-.-shift-.-.-.-.-]")
            {
                source.selected.indices = [];
                for (let i = 0; i < labels.length; i++) {
                    if (labels[i] == this.value) {
                        source.selected.indices.push(i);
                    }
                }
                source.change.emit();
            }
        }
    """,
        ),
    )

    # menu = [(o_c, o_c) for o_c in obs_string + obs_numerical]
    menu = obs_string + obs_numerical
    select_color_by = bokeh.models.Select(
        title="Color by (select field):", value="", options=menu, width=235
    )
    tooltip = bokeh.models.Tooltip(
        content="Ignores categorical fields with many different unique items (more "
        "than 70 or more than half the number of samples).\u00A0\u00A0",
        position="right",
    )
    help_button = bokeh.models.HelpButton(tooltip=tooltip, margin=(21, 0, 3, 0))

    select_color_by.on_change(
        "value",
        lambda attr, old, new: redefine_custom_legend(
            pb_plot,
            hidden_text_label_search,
            hidden_text_label_column,
            hidden_text_label_column_bis,
            hidden_legend_width,
            new,
            legend_dict,
            resize_width_input,
            obs_string,
            obs_numerical,
            bt_slider_range,
        ),
    )

    return select_color_by, help_button, hidden_text_label_column, hidden_legend_width
