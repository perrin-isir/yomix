# Contributing

In order to contibute to this repository you will need developer access to this repo. 
To know more about the project go to the [README](README.md) first.

## Pre-commit hooks

Pre-commits hooks have been configured for this project using the 
[pre-commit](https://pre-commit.com/) library:

- [black](https://github.com/psf/black) python formatter
- [flake8](https://flake8.pycqa.org/en/latest/) python linter

To get them going on your side, make sure to have python installed, and run the 
following commands from the root directory of this repository:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

These pre-commits are applied to all the files except those in folder tmp/
(see .pre-commit-config.yaml)
