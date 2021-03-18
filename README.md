<img src="https://github.com/F-Secure/pytest-rts/raw/master/docs/imgs/pytest-rts-logo.png" width="120px" height="120px"/>

# Coverage-based regression test selection (RTS) plugin for pytest

- [Usage](#usage)
- [Development](#dev)
- [Contributing](#contrib)

## <a name="usage"></a> Usage

### Usage as a module (no source code)

1. Install the module with `pip install pytest-rts`
2. Use the tool with `pytest --rts`

More detailed usage is described in the [tutorial][tutorial]

### Usage from source code

#### Initialization

1. Checkout the project
2. In project directory run `make install` - that will:
   - create virtual environment
   - download all the dependencies
   - install `pytest-rts`
3. Switch to directory with target project
4. Install all the dependencies needed for testing (should be installed into the same pytest-rts virtual environment)
5. Execute `pytest --cov=<path to code> --cov-context=test` which will run the entire test suite and build a mapping database with [pytest-cov](https://github.com/pytest-dev/pytest-cov)
6. Rename the coverage file produced by `pytest-cov` to your liking. Example: `mv .coverage pytest-rts-coverage`

#### Running new tests

1. execute `pytest --rts --rts-coverage-db=<your coverage file>` after adding new tests

## <a name="dev"></a> Development

See [DEVELOPER.md][developer] for more info

## <a name="contrib"></a> Contributing

### Contributing Guidelines

Read through our [contributing guidelines][contributing] to learn about our submission process, coding rules and more.

### Code of Conduct

Help us keep the project open and inclusive. Please read and follow our [Code of Conduct][codeofconduct].

## Acknowledgement

The package was developed by [F-Secure Corporation][f-secure] and [University of Helsinki][hy] in scope of [IVVES project][ivves]. This work was labelled by [ITEA3][itea3] and funded by local authorities under grant agreement “ITEA-2019-18022-IVVES”

[tutorial]: https://github.com/F-Secure/pytest-rts/tree/master/docs/tutorial.md
[developer]: https://github.com/F-Secure/pytest-rts/tree/master/docs/DEVELOPER.md
[contributing]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CONTRIBUTING.md
[codeofconduct]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CODE_OF_CONDUCT.md
[ivves]: http://ivves.eu/
[itea3]: https://itea3.org/
[f-secure]: https://www.f-secure.com/en
[hy]: https://www.helsinki.fi/en/computer-science
