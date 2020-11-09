# Building and Testing pytest-rts

This document describes how to set up your development environment to build and test the project.

* [Prerequisite Software](#prerequisite-software)
* [Getting the Sources](#getting-the-sources)
* [Installing NPM Modules](#installing-npm-modules)
* [Testing / linting with tox](#testing-linting)

See the [contribution guidelines](https://github.com/F-Secure/pytest-rts.git/docs/blob/master/CONTRIBUTING.md)
if you'd like to contribute to the project.


## Prerequisite Software

Before you can build and test the project, you must install and configure the
following products on your development machine:

* [Git](http://git-scm.com) and/or the **GitHub app** (for [Mac](http://mac.github.com) or [Windows](http://windows.github.com)); [GitHub's Guide to Installing Git](https://help.github.com/articles/set-up-git) is a good source of information.
* [Python 3.6](https://www.python.org/)
* [PIP](https://pypi.org/project/pip/)


## Getting the Sources

Fork and clone the repository:

1. Login to your GitHub account or create one by following the instructions given [here](https://github.com/signup/free).
2. [Fork](http://help.github.com/forking) the [main repository](https://github.com/F-Secure/pytest-rts).
3. Clone your fork of the repository and define an `upstream` remote pointing back to
   the repository that you forked in the first place.

```shell
# Clone your GitHub repository:
git clone git@github.com:<github username>/pytest-rts.git

# Go to the project directory:
cd pytest-rts

# Add the main repository as an upstream remote to your repository:
git remote add upstream https://github.com/F-Secure/pytest-rts.git
```


## <a name="testing-lint"></a> Testing / linting with tox

Make sure you have Python versions 3.6, 3.7, 3.8, 3.9 (all of them). Install tox
into your current Python environment (does not matter which one it is). Run
`tox` to run linters/tests using different Python versions. To run for only one
Python version, use, for example, `tox -e py36`. To check code formatting with
black, run `tox -e py38-check-format` (code formatting check is done only with
Python 3.8).

**NB** If you have changed dependencies in `setup.py`, run `tox --recreate`
once.
