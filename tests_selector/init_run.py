import pytest
import os
import sys

from tests_selector.pytest.my_pytest_plugin import MyPytestPlugin


def main():
    project_folder = sys.argv[1]
    os.chdir(os.getcwd() + "/" + project_folder)
    pytest.main([], plugins=[MyPytestPlugin()])


if __name__ == "__main__":
    main()
