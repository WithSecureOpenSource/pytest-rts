import pytest
import os
import sys

from tests_selector.pytest.init_phase_plugin import InitPhasePlugin


def main():
    project_folder = sys.argv[1]
    os.chdir(os.getcwd() + "/" + project_folder)
    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
