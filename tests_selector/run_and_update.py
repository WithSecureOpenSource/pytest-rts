import pytest
import sys

from tests_selector.pytest.update_phase_plugin import UpdatePhasePlugin


def main():
    test_set = set(sys.argv[1:])
    pytest.main([], plugins=[UpdatePhasePlugin(test_set)])


if __name__ == "__main__":
    main()
