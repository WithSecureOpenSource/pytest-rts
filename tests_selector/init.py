import pytest

from tests_selector.pytest.init_phase_plugin import InitPhasePlugin


def main():
    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
