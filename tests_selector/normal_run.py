import os
import pytest
import sys

from tests_selector.pytest.normal_phase_plugin import NormalPhasePlugin


def main():
    project_folder = sys.argv[1]
    os.chdir(os.getcwd() + "/" + project_folder)
    test_set = set(sys.argv[2:])
    pytest.main([], plugins=[NormalPhasePlugin(test_set)])


if __name__ == "__main__":
    main()
