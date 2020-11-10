"""This module contains code for running pytest with UpdatePhasePlugin"""
import sys
import pytest
from pytest_rts.pytest.update_phase_plugin import UpdatePhasePlugin


def main():
    """Run pytest with UpdatePhasePlugin and a given test set"""
    test_set = set(sys.argv[1:])
    pytest.main([], plugins=[UpdatePhasePlugin(test_set)])


if __name__ == "__main__":
    main()
