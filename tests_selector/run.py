import pytest
import sys

from tests_selector.pytest.normal_phase_plugin import NormalPhasePlugin


def main():
    test_set = set(sys.argv[1:])
    pytest.main([], plugins=[NormalPhasePlugin(test_set)])


if __name__ == "__main__":
    main()
