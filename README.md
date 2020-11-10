<img src="https://github.com/F-Secure/pytest-rts/raw/master/docs/pytest-rts-logo.png" width="120px" height="120px"/>

# Change based tests selection for Python

 - [Usage](#usage)
 - [Development](#dev)
 - [Contributing](#contrib)

## <a name="usage"></a> Usage

### Usage as a module (no source code)

1. Add your public key to github profile
2. Add `git+ssh://git@github.com/F-Secure/pytest-rts.git#egg=pytest-rts` as a dependency to `requirements.txt`
3. Install dependencies
4. Run initialization `pytest_rts_init`

### Usage from source code

#### Initialization

1. Checkout the project
2. In project directory run `make install` - that will:
   - create virtual environment
   - download all the dependencies
   - install `pytest_rts` as a tool
3. Switch to directory with target project
4. Install all the dependencies needed for testing (should be installed into the same pytest_rts virtual environment)
5. Execute `pytest_rts_init`

#### Running tests related to the changes

1. switch to directory with target project
2. execute `pytest_rts`

#### Running evaluation code

1. execute `pytest_rts_eval` in target project directory

## <a name="dev"></a> Development

See [DEVELOPER.md](developer) for more info

## <a name="contrib"></a> Contributing

### Contributing Guidelines

Read through our [contributing guidelines][contributing] to learn about our submission process, coding rules and more.

### Code of Conduct

Help us keep the project open and inclusive. Please read and follow our [Code of Conduct][codeofconduct].


[developer]: https://github.com/F-Secure/pytest-rts/tree/master/docs/DEVELOPER.md
[contributing]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CONTRIBUTING.md
[codeofconduct]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CODE_OF_CONDUCT.md
