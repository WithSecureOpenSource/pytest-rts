<img src="https://github.com/F-Secure/pytest-rts/raw/master/docs/imgs/pytest-rts-logo.png" width="120px" height="120px"/>

# Coverage-based regression test selection (RTS) plugin for pytest

- [Usage](#usage)
- [Development](#dev)
- [Contributing](#contrib)

## <a name="usage"></a>Usage

Plugin is supposed to be used to execute tests related to changes done locally on developer's machine and in CI environment to test pull requests.

### Initialization

To start using pytest-rts build of coverage DB is needed. For [Trunk Based Development](https://trunkbaseddevelopment.com/) mapping database from `master` branch should be used, for [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/) - `develop`

1. Install [pytest-cov](https://github.com/pytest-dev/pytest-cov) with `pip install pytest-cov`
2. Configure coverage with `.coveragerc`:
   ```dosini
   [run]
   source = <path to your package>
   relative_files = True
   dynamic_context = test_function
   ```
2. Execute `pytest --cov-config=.coveragerc` which will run the entire test suite and build a mapping database
3. Rename the coverage file `.coverage` produced by `pytest-cov` to your liking. Example: `mv .coverage pytest-rts-coverage`

### Usage

1. Install `pytest-rts` with `pip install pytest-rts`
2. Create a branch `git checkout -b feat/new-feature`
3. Make changes in your code
5. Run the tool with `pytest --rts --rts-coverage-db=[path to database]`

As a result only tests related to made changes will be executed.

### Usage in CI

* In the main branch (`master` or `develop`) make sure you run entire test suite and
  * commit back coverage database
  * or, if the database size is big, upload it to some storage
* In pull requests:
  * make sure you have coverage database from the main branch located next to the code
  * run `pytest --rts --rts-coverage-db=[path to database]`

## <a name="dev"></a> Development

See [DEVELOPER.md][developer] for more info

## <a name="contrib"></a> Contributing

### Contributing Guidelines

Read through our [contributing guidelines][contributing] to learn about our submission process, coding rules and more.

### Code of Conduct

Help us keep the project open and inclusive. Please read and follow our [Code of Conduct][codeofconduct].

## Acknowledgement

The package was developed by [F-Secure Corporation][f-secure] and [University of Helsinki][hy] in scope of [IVVES project][ivves]. This work was labelled by [ITEA3][itea3] and funded by local authorities under grant agreement “ITEA-2019-18022-IVVES”

[developer]: https://github.com/F-Secure/pytest-rts/tree/master/docs/DEVELOPER.md
[contributing]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CONTRIBUTING.md
[codeofconduct]: https://github.com/F-Secure/pytest-rts/tree/master/docs/CODE_OF_CONDUCT.md
[ivves]: http://ivves.eu/
[itea3]: https://itea3.org/
[f-secure]: https://www.f-secure.com/en
[hy]: https://www.helsinki.fi/en/computer-science
