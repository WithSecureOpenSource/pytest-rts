"""Tests for common utility functions"""
from typing import cast

import pytest
from _pytest.nodes import Item

from pytest_rts.utils.common import filter_pytest_items, strip_pytest_cov_testname


@pytest.mark.parametrize(
    "testname, expected",
    [
        (
            "tests/test_example.py::test_methods_var_inheritance|setup",
            "tests/test_example.py::test_methods_var_inheritance",
        ),
        (
            "tests/test_example2.py::TestJSON::test_jsonify_basic_types[0]|teardown",
            "tests/test_example2.py::TestJSON::test_jsonify_basic_types[0]",
        ),
        (
            "tests/test_example3.py::test_session_ip_warning|run",
            "tests/test_example3.py::test_session_ip_warning",
        ),
    ],
)
def test_strip_pytest_cov_testname(testname: str, expected: str) -> None:
    """Test pytest-cov testname stripping to actual pytest item.nodeid strings"""
    assert strip_pytest_cov_testname(testname) == expected


def test_filter_pytest_items() -> None:
    """Test for filtering the test set
    based on given existing tests
    """

    class FakePytestItem:  # pylint: disable=too-few-public-methods
        """Class that has nodeid field like a pytest item
        and a method get_closest_marker which returns something
        """

        def __init__(self, name: str, nodeid: str, markername: str) -> None:
            """Set test name, identifier nodeid and marker name"""
            self.name = name
            self.nodeid = nodeid
            self.markername = markername

        def get_closest_marker(self, markername: str) -> bool:
            """Return if item is marked as skipped"""
            if self.markername == markername:
                return True
            return False

    collected_items = [
        cast(Item, FakePytestItem("test1", "test_func_1", "")),
        cast(Item, FakePytestItem("test2", "test_func_2", "skip")),
        cast(Item, FakePytestItem("test3", "test_func_3", "")),
        cast(Item, FakePytestItem("test4", "test_func_4", "skipif")),
        cast(Item, FakePytestItem("test5", "test_func_5", "")),
    ]
    existing_tests = {
        "test_func_1",
        "test_func_3",
    }

    filtered_items = filter_pytest_items(collected_items, existing_tests)

    assert len(filtered_items) == 1
    assert filtered_items[0].nodeid == "test_func_5"
