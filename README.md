# Change based tests selection for Python

## Usage

### Usage as a module (no source code)

1. Add your public key to github profile
2. Add `git+ssh://git@github.com/F-Secure/tests-selector.git#egg=tests_selector` as a dependency to `requirements.txt`
3. Install dependencies
4. Run initialization `tests_selector_init`

### Usage from source code

#### Initialization

1. Checkout the project
2. In project directory run `make install` - that will:
   - create virtual environment
   - download all the dependencies
   - install `tests_selector` as a tool
3. Switch to directory with target project
4. Install all the dependencies needed for testing (should be installed into the same tests_selector virtual environment)
5. Execute `tests_selector_init`

#### Running tests related to the changes

1. switch to directory with target project
2. execute `tests_selector`

#### Running evaluation code

1. execute `tests_selector_eval` in target project directory

# Development

- ~~Don't forget to run `make install` before you are going to try the latest changes~~ - not needed as all the changes in source files are available immediately, just call the needed command line tool from the package

## Testing / linting with tox

Make sure you have Python versions 3.6, 3.7, 3.8, 3.9 (all of them). Install tox
into your current Python environment (does not matter which one it is). Run
`tox` to run linters/tests using different Python versions. To run for only one
Python version, use, for example, `tox -e py36`. To check code formatting with
black, run `tox -e py38-check-format` (code formatting check is done only with
Python 3.8).

**NB** If you have changed dependencies in `setup.py`, run `tox --recreate`
once.
