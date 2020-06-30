# First implementation

## Current state of implementation

 * Only using SQLite database created by Coverage.py and copying data from there to own database
 
 * Files considered are extracted from the file list that Coverage finds
 
 * Specifying the files can be done with .coveragerc file (file to specify which files are checked by Coverage)
 
 * Example .coveragerc -file found for "flask" project in current folder named "2" 
 
 * Reads gits changes, finds tests, runs tests, adds git changes, updates database like demoed
 
## Problems

* Mapping context to actual tests is a bit difficult and haven't gotten it working perfectly. Now I've commented out a function that was supposed to find all tests from changed test files but didn't get it working because of difficulties in guessing what contexts belong to a specific test file. 
 
Examples of problems:
```
Coverage contexts:
7926|template_tests.filter_tests.test_default.FunctionTests.test_empty_string
7929|template_tests.filter_tests.test_default_if_none.FunctionTests.test_empty_string

pytest module finds:
tests/template_tests/filter_tests/test_default.py::FunctionTests::test_empty_string

== mappings get messed up in cases where there's no unique match







Coverage context:
flask.app.Flask.test_request_context

Not a test and pytest doesn't find anything similar


+ many more related to different project structures and how contexts are generated
```

* Complicated test runners for big projects (ie. Django, Spark) cause errors with some global variables and have made testing this difficult
