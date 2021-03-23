<img src="https://github.com/F-Secure/pytest-rts/raw/master/docs/imgs/pytest-rts-logo.png" width="120px" height="120px"/>

# Coverage-based regression test selection (RTS) plugin for pytest

- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Development](#dev)
- [Contributing](#contrib)

## <a name="usage"></a> Usage

Plugin is supposed to be used to execute tests related to changes done locally on developer's machine and in CI environment to test pull requests.

### Initialization

To start using pytest-rts build of coverage DB is needed. For [Trunk Based Development](https://trunkbaseddevelopment.com/) mapping database from `master` branch should be used, for [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/) - `develop`

1. Install [pytest-cov](https://github.com/pytest-dev/pytest-cov) with `pip install pytest-cov`
2. Create a `.coveragerc` file with the following contents inside to configure `pytest-cov`:
```
[run] 
relative_files = True
```
 
3. Execute `pytest --cov=[path to your package] --cov-context=test` which will run the entire test suite and build a mapping database in `.coverage` file
4. Rename the coverage file `.coverage` produced by `pytest-cov` to your liking. Example: `mv .coverage pytest-rts-coverage`

### Local usage

1. Install `pytest-rts` with `pip install pytest-rts`
2. Create a branch `git checkout -b feat/new-feature`
3. Make changes in your code
4. Run the tool with `pytest --rts --rts-coverage-db=[path to database]`

As a result only tests related to changes in working directory and branch will be executed.

### Usage in CI

* In the main branch (`master` or `develop`) make sure you run entire test suite and
  * commit back coverage database
  * or, if the database size is big, upload it to some storage
* In pull requests:
  * make sure you have coverage database from the main branch located next to the code
  * run `pytest --rts --rts-coverage-db=[path to database]`

## <a name="troubleshooting"></a> Troubleshooting

* **`pytest --rts` returns non-zero code:** command returns one of the
  [pytest exit codes](https://docs.pytest.org/en/stable/usage.html#possible-exit-codes). For example if pytest-rts
  module found no tests to execute resulting code will be 5 "No tests were collected"

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
