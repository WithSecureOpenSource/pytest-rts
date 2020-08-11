import pytest

from tests_selector.pytest.init_phase_plugin import InitPhasePlugin
from tests_selector.utils.common import check_create_coverage_conf


def main():
    check_create_coverage_conf()
    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
