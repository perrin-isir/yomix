""" Enable execution of the "yomix" command line program with the ``-m``
switch. For example:

.. code-block:: sh

    python -m yomix myfile.h5ad

is equivalent to

.. code-block:: sh

    yomix myfile.h5ad

"""

import yomix
from tornado.ioloop import IOLoop
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.server.server import Server
from pathlib import Path
import argparse

__all__ = ("main",)


def main():

    parser = argparse.ArgumentParser(description="Yomix command-line tool")

    parser.add_argument(
        "file", type=str, nargs="?", default=None, help="the .ha5d file to open"
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=5006,
        help="port on which the app should run",
    )

    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default="",
        help="name given to the main plot",
    )

    parser.add_argument(
        "--subsampling",
        type=int,
        help="randomly subsample the dataset to a maximum number of observations "
        "(=SUBSAMPLING)",
    )
    parser.add_argument(
        "--example", action="store_true", help="use the example dataset"
    )

    args = parser.parse_args()

    argument = args.example

    if argument:
        filearg = Path(__file__).parent / "example" / "pbmc.h5ad"
    else:
        assert (
            args.file is not None
        ), "yomix: error: the following arguments are required: file"
        filearg = Path(args.file)

    if filearg.exists():

        modify_doc = yomix.server.gen_modify_doc(filearg, args.subsampling, args.name)

        io_loop = IOLoop.current()

        bokeh_app = Application(FunctionHandler(modify_doc))

        server = Server({"/": bokeh_app}, io_loop=io_loop, port=args.port)
        server.start()

        print(f"Opening Yomix on http://localhost:{args.port}/\n")

        io_loop.add_callback(server.show, "/")
        io_loop.start()
