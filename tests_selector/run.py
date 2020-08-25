import pytest
import sys

from tests_selector.pytest.normal_phase_plugin import NormalPhasePlugin


def main():
    pytest_param = [sys.argv[1]] if sys.argv[1] == "-x" else []
    test_set = set(sys.argv[2:])
    pytest.main(pytest_param, plugins=[NormalPhasePlugin(test_set)])


if __name__ == "__main__":
    main()
