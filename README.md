# Change based tests selection for Python

## Material found on regression test selection

### Tools

| Name | What?| Last updated | Link to code  / website | Link to article / paper |
|------|--------------|--------------|------------------------|-------------------------|
| RETECS | Reinforcement learning for test case selection and prioritization. Uses historic test run data (results, test duration, execution times). "Lightweight method". | 2018 | [BitBucket](https://bitbucket.org/HelgeS/retecs/src/master/) | Paper: [Reinforcement Learning for Automatic Test Case Prioritization and Selection in Continuous Integration](https://arxiv.org/pdf/1811.04122.pdf) |
|HyRTS|Regression test selection for java. Tries to combine method-level and file-level change detection. Maven plugin provided but no source code. | 2018 |[Website](http://hyrts.org/) | Paper: [Hybrid Regression Test Selection](https://personal.utdallas.edu/~lxz144130/publications/icse2018.pdf) |
|JUnit4Git|File-level regression test selection for JVM projects (maven/gradle). Uses git data and works by creating "git notes" to repository.|2019|[Github repo](https://github.com/rpau/junit4git)| - |
|TestMon|Pytest plugin for selecting and running affected tests.|2019|[Github repo](https://github.com/tarpas/pytest-testmon)|-|
|Jest | Facebook's testing framework Jest runs only affected tests by default. Considers changes on file-level with git diff.|2020|[Website](https://jestjs.io/)|-|

### Articles/papers

| Title | Year | What? | Link |
|-------|------|-------|------|
|Predictive test selection | 2018 | Facebook's regression test selection with machine learning. Based on gradient boosted decision trees classifier (XGBoost) and historical data. |[paper](https://arxiv.org/pdf/1810.05286.pdf)|
|Understanding and Improving Regression Test Selection in Continuous Integration|2019|Compare regression test selection methods in CI environment. Class-level dependencies,method-level dependencies and hybrid method.|[paper](http://mir.cs.illinois.edu/awshi2/publications/ISSRE2019.pdf)|
|Automating Root Cause Analysis via Machine Learning in Agile Software Testing Environments|2019|Machine learning to categorize causes of failed tests | [paper](https://acris.aalto.fi/ws/portalfiles/portal/35606292/SCI_Kahles_Torronen_Huuhtanen_Jung_Automating_Root_2019_RCA_ML_SW.pdf)|
|Scalable Approaches for Test Suite Reduction|2019|Similarity based selection of regression tests compared | [paper](https://robertoverdecchia.github.io/papers/ICSE_2019.pdf)|
|Improving Continuous Integration with Similarity-based Test Case Selection|2018|Selecting subsets of tests based on similarity|[paper](https://www.diva-portal.org/smash/get/diva2:1196682/FULLTEXT01.pdf)|
|Obtaining Coverage per Test Case|2017|Obtaining per-test coverage in Java for regression testing|[paper](https://www.cqse.eu/fileadmin/content/news/publications/2017-obtaining-coverage-per-test-case.pdf)|


## Current state of implementation

* Some code to try supporting git history data, builds database by looping through commits. No evaluation metric in place at the moment.
* Another evaluation method tested: Removing random lines from source files and checking the exit codes of running specific tests and all tests, currently just stores the exit codes in database.
* Test functions are now also mapped to lines of code. Testfile is parsed and function lines are extracted. If a testfile has changes, only the affected changes are considered.
* I've had success with "flask" (around 4000 commits) and "rich" (around 700 commits) from github.
 
## Usage

### Initialization

1. checkout the project
2. in project directory run `make install` - that will:
  * create virtual environment
  * download all the dependencies
  * install `tests_selector` as a tool
3. switch to directory with target project
4. install all the dependencies needed for testing (should be installed into the same tests_selector virtual environment)
5. go back to `tests_selector` directory
6. execute `tests_selector_init path/to/target_project`

### Running tests related to the changes

1. switch to directory with target project
2. execute `tests_selector`

# Development

* ~~Don't forget to run `make install` before you are going to try the latest changes~~ - not needed as all the changes in source files are available immediately, just call the needed command line tool from the package
