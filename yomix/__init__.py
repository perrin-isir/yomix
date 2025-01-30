from . import plotting, tools, server
import sys
from pathlib import Path

__version__ = Path(__file__).with_name("VERSION").read_text().strip()

sys.modules.update(
    {f"{__name__}.{m}": globals()[m] for m in ["plotting", "tools", "server"]}
)
