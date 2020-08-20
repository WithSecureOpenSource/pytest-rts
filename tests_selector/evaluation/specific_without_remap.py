import os
import pytest
import sys

from tests_selector.pytest.capture_specific_plugin import CaptureSpecificPlugin


def main():
    PROJECT_FOLDER = sys.argv[1]
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    test_set = set(sys.argv[2:])
    exit_code = pytest.main(
        ["-p", "no:terminal"], plugins=[CaptureSpecificPlugin(test_set)]
    )
    exit(int(exit_code))


if __name__ == "__main__":
    main()
