import os
import pytest
import sys

from tests_selector.pytest.capture_all_plugin import CaptureAllPlugin


def main():
    PROJECT_FOLDER = sys.argv[1]
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    pytest.main(["-p", "no:terminal"], plugins=[CaptureAllPlugin()])


if __name__ == "__main__":
    main()
