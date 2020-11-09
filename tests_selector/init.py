"""This module contains code for running pytest with InitPhasePlugin"""
import pytest
from tests_selector.pytest.init_phase_plugin import InitPhasePlugin


def main():
    """Run pytest with InitPhasePlugin"""
    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
