"""This module contains code for collecting newly added tests from pytest"""
import sys

import pytest

from pytest_rts.pytest.collect_plugin import CollectPlugin

connection_string = sys.argv[1]


def main():
    """Collect newly added tests and store them to database with pytest --collect-only"""
    pytest.main(
        ["--collect-only", "-p", "no:terminal"],
        plugins=[CollectPlugin(connection_string)],
    )


if __name__ == "__main__":
    main()
