# First implementation

## Current state of implementation (folder 3)

* Some code to try supporting git history data, builds database by looping through commits. No evaluation metric in place at the moment.

* Another evaluation method tested: Removing random lines from source files and checking the exit codes of running specific tests and all tests, currently just stores the exit codes in database.

* Test functions are now also mapped to lines of code. Testfile is parsed and function lines are extracted. If a testfile has changes, only the affected changes are considered.
 

## How I've used this

* Copy all the files from folder 3

* Clone some python project to the same folder, project should be a subfolder. I've had success with "flask" (around 4000 commits) and "rich" (around 700 commits) from github.

* make a virtual environment and install projects depencies + "pip install pydriller" + "pip install coverage" + "pip install pytest".

* ```python start.py PROJECT_FOLDER``` starts the program. Example: ```python start.py rich``` for a project I used to test this.
