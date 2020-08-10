import os

import pytest

from tests_selector.helper import COVERAGE_CONF_FILE_NAME
from tests_selector.pytest.init_phase_plugin import InitPhasePlugin


def main():
    if not os.path.isfile(COVERAGE_CONF_FILE_NAME):
        with open(COVERAGE_CONF_FILE_NAME, "w") as coverage_config_file:
            coverage_config_file.writelines(
                ["[run]", "omit = */.venv/*, tests/*, /tmp/*, *__init__*"]
            )

    pytest.main([], plugins=[InitPhasePlugin()])


if __name__ == "__main__":
    main()
