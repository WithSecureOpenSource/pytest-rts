# Tutorial on using pytest-rts in an open source project

## Requirements

* Python  >= 3.6.6
* Git

## Setting up

This tutorial uses [flask](https://github.com/pallets/flask) (version `1.1.2`) as an example.

1. Clone [flask](https://github.com/pallets/flask) and install the dependencies + `pytest-rts`
![install dependencies](./imgs/tutorial/install_flask.png)
2. Follow the steps in [README](../README.md) to configure and build the mapping database
![configure coverage](./imgs/tutorial/configure.png)
![run all tests](./imgs/tutorial/first_run1.png)
![test results](./imgs/tutorial/first_run2.png)

## Use the test selection feature

Follow the steps in [README](../README.md) to use pytest-rts. Screenshots illustrate the outcome with simple changes.

1. Change a file and run the tests for it
![working directory run](./imgs/tutorial/workdir_change1.png)
2. Commit changes to a new branch
![commit first change](./imgs/tutorial/commit_change1.png)
3. Change another file and run tests for it
![working directory run 2](./imgs/tutorial/workdir_change2.png)
4. Commit the second change
![commit second change](./imgs/tutorial/commit_change2.png)
5. Run tests for both commits
![run tests for committed changes](./imgs/tutorial/run_committed.png)
