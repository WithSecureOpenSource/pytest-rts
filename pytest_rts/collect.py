"""This module contains code for collecting newly added tests from pytest"""
import pytest
from pytest_rts.pytest.collect_plugin import CollectPlugin


def main():
    """Collect newly added tests and store them to database with pytest --collect-only"""
    pytest.main(["--collect-only", "-p", "no:terminal"], plugins=[CollectPlugin()])


if __name__ == "__main__":
    main()
