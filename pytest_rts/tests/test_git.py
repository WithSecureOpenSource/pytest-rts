"""Unittests for Git functionality"""
from pytest_rts.utils.git import get_changed_lines


def test_get_changed_lines() -> None:
    """Test case for reading changed lines from git diff -U0 output"""
    diff = """diff --git a/pytest_rts/utils/common.py b/pytest_rts/utils/common.py
            index 43d1651..63be8a8 100644
            --- a/pytest_rts/utils/common.py
            +++ b/pytest_rts/utils/common.py
            @@ -18 +18 @@ def filter_pytest_items(
            -    return list(
            +    return list(set(
            @@ -21,0 +22,2 @@ def filter_pytest_items(
            +
            +                new_var = 1
            @@ -42,2 +43,0 @@ def get_existing_tests(coverage_file_path: str) -> Set[str]:
            -
            -
            @@ -86 +85,0 @@ def strip_pytest_cov_testname(testname: str) -> str:
            -    return testname
    """
    changed_lines = get_changed_lines(diff)
    assert changed_lines == {18, 21, 42, 43, 86}
