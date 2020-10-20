# Tutorial on running this tool on an open source project

## Requirements

* Python 3.8+
* Git

## Setting up

This tutorial uses [flask](https://github.com/pallets/flask) as an example. At the time of writing, flask has a set of 487 tests with pytest.

1. Clone [flask](https://github.com/pallets/flask) and this repository (**tests-selector**) to their own folders.
2. In the root of this repository, run `make install` which creates a virtualenv and activate it with `source .venv/bin/activate`
3. Go to the flask repository folder and install its dependencies. At the time of writing, this is done with `pip install -e . -r requirements/dev.txt`
4. Run `tests_selector_init` to initialize the mapping database

## Usage

* Change some source code file or test file -> run `tests_selector` -> the tool runs tests based on changes in the git working directory
* Change some source code file or test file -> commit changes -> run `tests_selector` -> the tool runs tests based on changes between the current commit state and the time the mapping database was last updated & updates the database
