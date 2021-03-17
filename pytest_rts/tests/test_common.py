"""Tests for common utility functions"""

import pytest

from pytest_rts.utils.common import strip_pytest_cov_testname


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
def test_strip_pytest_cov_testname(testname, expected):
    """Test pytest-cov testname stripping to actual pytest item.nodeid strings"""
    assert strip_pytest_cov_testname(testname) == expected
