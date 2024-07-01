# Install with 'pip install -e .'

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="yomix",
    version=Path(__file__).with_name("VERSION").read_text().strip(),
    description="yomix: an interactive tool to explore low dimensional "
    "embeddings of omics data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/perrin-isir/yomix",
    packages=find_packages(),
    include_package_data=True,
    license="LICENSE",
)
