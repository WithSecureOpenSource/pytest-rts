import pytest

from tests_selector.helper import check_create_coverage_conf
from tests_selector.pytest.init_phase_plugin import InitPhasePlugin


def main():
    check_create_coverage_conf()
    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
