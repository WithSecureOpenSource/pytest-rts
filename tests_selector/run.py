"""This module contains code for running pytest with NormalPhasePlugin"""
import sys
import pytest
from tests_selector.pytest.normal_phase_plugin import NormalPhasePlugin


def main():
    """Run pytest with NormalPhasePlugin and a given test set"""
    test_set = set(sys.argv[1:])
    pytest.main([], plugins=[NormalPhasePlugin(test_set)])


if __name__ == "__main__":
    main()
