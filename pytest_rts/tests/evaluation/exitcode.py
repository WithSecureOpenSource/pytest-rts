"""This module contains code to capture pytest exitcode for the given test set"""
import sys
import pytest
from pytest_rts.tests.evaluation.capture_specific_plugin import CaptureSpecificPlugin


def main():
    test_set = set(sys.argv[1:])
    exit_code = pytest.main(
        ["-p", "no:terminal"], plugins=[CaptureSpecificPlugin(test_set)]
    )
    exit(int(exit_code))


if __name__ == "__main__":
    main()
