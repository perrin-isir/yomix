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
import subprocess
import sys
import time

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
    parser.add_argument(
        "--dev", action="store_true", help="auto-reload server when source files change"
    )

    args = parser.parse_args()

    if args.dev:
        watch_dir = Path(__file__).resolve().parent
        forward_args = [a for a in sys.argv[1:] if a != "--dev"]

        def get_mtimes():
            result = {}
            for f in watch_dir.rglob("*.py"):
                try:
                    result[str(f)] = f.stat().st_mtime
                except OSError:
                    pass
            return result

        def start_server():
            return subprocess.Popen([sys.executable, "-m", "yomix"] + forward_args)

        mtimes = get_mtimes()
        proc = start_server()
        print(f"[dev] Server started. Watching {watch_dir} for changes …", flush=True)
        try:
            while True:
                time.sleep(1)
                new_mtimes = get_mtimes()
                changed = [
                    Path(f).name
                    for f in new_mtimes
                    if new_mtimes[f] != mtimes.get(f)
                ]
                if changed:
                    print(
                        f"[dev] Changed: {', '.join(changed)} — restarting …",
                        flush=True,
                    )
                    mtimes = new_mtimes
                    proc.terminate()
                    proc.wait()
                    proc = start_server()
        except KeyboardInterrupt:
            print("[dev] Stopping.", flush=True)
            proc.terminate()
        return

    argument = args.example

    if argument:
        filearg = (Path(__file__).resolve().parent / "example" / "pbmc.h5ad")
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


if __name__ == "__main__":
    main()
