''' Enable execution of the "yomix" command line program with the ``-m``
switch. For example:

.. code-block:: sh

    python -m yomix myfile.h5ad

is equivalent to

.. code-block:: sh

    yomix myfile.h5ad

'''

import yomix
import numpy as np
import bokeh.layouts
import anndata
from scipy.sparse import issparse
from tornado.ioloop import IOLoop
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.server.server import Server
from pathlib import Path
import sys

__all__ = (
    'main',
)

def main():
    if len(sys.argv) < 2:
        sys.exit("Missing argument (input file).")

    argument = sys.argv[1]

    if argument == "--example":
        filearg = Path(__file__).parent / "example" / "pbmc.h5ad"
    else:
        filearg = Path(argument)
    
    if filearg.exists():
        xd = anndata.read_h5ad(filearg.absolute())        

        def _to_dense(x):
            if issparse(x):
                return x.todense()
            else:
                return x

        xd.X = np.asarray(_to_dense(xd.X))

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
                    name="bt_select_embedding"
                )

                if embedding_key != "":

                    embedding_size = xd.obsm[embedding_key].shape[1]
                    assert embedding_size > 1

                    (
                        obs_string, obs_numerical, points_bokeh_plot, 
                        bt_slider_point_size, bt_slider_yaw, bt_slider_pitch, 
                        bt_slider_roll, resize_width_input, resize_height_input,
                        source_rotmatrix_etc, div_sample_names, sample_search_input,
                        sl_component1, sl_component2, sl_component3
                    ) = yomix.plotting.main_figure(xd, embedding_key, 800, 550, "")

                    (
                        bt_A, toggle_A, hidden_checkbox_A, bt_B, toggle_B, 
                        hidden_checkbox_B, bt_AplusB, bt_nothing
                    ) = yomix.tools.subset_buttons(points_bokeh_plot, 
                                                  source_rotmatrix_etc)

                    (
                        select_color_by,
                        hidden_text_label_column,
                        hidden_legend_width) = yomix.plotting.setup_legend(
                            points_bokeh_plot,
                            obs_string, obs_numerical,
                            source_rotmatrix_etc,
                            resize_width_input)

                    offset_text_feature_color = yomix.plotting.color_by_feature_value(
                        points_bokeh_plot,
                        xd,
                        select_color_by,
                        hidden_text_label_column,
                        resize_width_input,
                        hidden_legend_width)

                    (
                        bt_sign1,
                        bt_sign2,
                        multiselect_signature,
                        div_signature_list,
                        sign_nr
                    ) = yomix.tools.signature_buttons(
                            xd, offset_text_feature_color, 
                            hidden_checkbox_A, hidden_checkbox_B)

                    bt_open_link = yomix.tools.gene_query_button(
                        offset_text_feature_color)

                    bt_sign3 = yomix.tools.arrow_function(
                        points_bokeh_plot,
                        xd,
                        embedding_key,
                        bt_slider_roll,
                        bt_slider_pitch,
                        bt_slider_yaw,
                        source_rotmatrix_etc,
                        hidden_checkbox_A,
                        div_signature_list,
                        multiselect_signature,
                        sign_nr,
                        sl_component1,
                        sl_component2,
                        sl_component3
                    )

                    c1div = bokeh.models.Div(text="Component X:")
                    c2div = bokeh.models.Div(text="Component Y:")
                    c3div = bokeh.models.Div(text="Component Z:")

                    if embedding_size == 2:
                        bt_slider_yaw.visible = False
                        bt_slider_pitch.visible = False
                        c3div.visible = False

                    p = (
                        bokeh.layouts.row(
                            bokeh.layouts.column(
                                bt_select_embedding,
                                bokeh.layouts.row(resize_height_input, 
                                                  resize_width_input),
                                select_color_by,
                                bokeh.layouts.row(bt_A, toggle_A),
                                bokeh.layouts.row(bt_B, toggle_B),
                                bokeh.layouts.row(bt_nothing, bt_AplusB),
                                bt_sign1,
                                bt_sign2,
                                bt_sign3,
                                multiselect_signature,
                                div_signature_list
                            ),
                            (bokeh.layouts.column(
                                points_bokeh_plot,
                                bokeh.layouts.row(
                                    bokeh.layouts.row(
                                        bokeh.layouts.column(
                                            bt_slider_point_size,
                                            bt_slider_roll,
                                            bt_slider_yaw),
                                        bt_slider_pitch),
                                    bokeh.layouts.column(
                                        bokeh.layouts.row(offset_text_feature_color, 
                                                        bt_open_link),
                                        bokeh.layouts.row(sample_search_input, 
                                                        div_sample_names),
                                    )
                                ),
                                bokeh.layouts.row(
                                    bokeh.layouts.column(
                                        c1div, c2div, c3div
                                    ),
                                    bokeh.layouts.column(
                                        sl_component1,
                                        sl_component2,
                                        sl_component3
                                    )
                                )
                            )  if sl_component1 is not None else 
                                bokeh.layouts.column(
                                    points_bokeh_plot,
                                    bokeh.layouts.row(
                                        bokeh.layouts.row(
                                            bokeh.layouts.column(
                                                bt_slider_point_size,
                                                bt_slider_roll,
                                                bt_slider_yaw),
                                            bt_slider_pitch),
                                        bokeh.layouts.column(
                                            bokeh.layouts.row(offset_text_feature_color, 
                                                            bt_open_link),
                                            bokeh.layouts.row(sample_search_input, 
                                                            div_sample_names),
                                        )
                                    )
                                )
                            )
                        )
                    )
                
                else:
                    p = (
                        bokeh.layouts.row(
                            bt_select_embedding
                        )
                    )

                return p

            def reset_figure(new):
                doc.clear()
                p_new = build_figure(new)
                p_new.select_one(dict(name="bt_select_embedding")).on_change(
                    "value",
                    lambda attr, old, new: reset_figure(new)
                )
                doc.add_root(p_new)

            p_0 = build_figure(None)
            p_0.select_one(dict(name="bt_select_embedding")).on_change(
                "value",
                lambda attr, old, new: reset_figure(new)
            )

            doc.add_root(p_0)

        io_loop = IOLoop.current()

        bokeh_app = Application(FunctionHandler(modify_doc))

        server = Server({'/': bokeh_app}, io_loop=io_loop)
        server.start()

        print('Opening yomix application on http://localhost:5006/\n')

        io_loop.add_callback(server.show, "/")
        io_loop.start()