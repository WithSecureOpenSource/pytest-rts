"""Unittests for Git functionality"""

from typing import List

import pytest

from pytest_rts.tests.fake_diffs import FAKE_DIFF_1, FAKE_DIFF_2, FAKE_DIFF_3
from pytest_rts.utils.git import get_changed_lines


@pytest.mark.parametrize(
    "diff, real_changed_lines",
    [
        (
            FAKE_DIFF_1,
            [
                23,
                29,
                30,
                34,
                35,
                36,
                38,
                40,
                50,
                59,
                67,
                72,
                83,
                91,
                100,
                109,
                119,
                135,
                145,
                161,
                171,
                181,
                190,
                199,
                210,
                219,
                228,
                238,
            ],
        ),
        (FAKE_DIFF_2, [83, 240]),
        (FAKE_DIFF_3, [16, 24]),
    ],
)
def test_get_changed_lines(diff: str, real_changed_lines: List[int]) -> None:
    """Test case for reading changed lines from git diff -U0 output"""
    changed_lines = get_changed_lines(diff)
    assert changed_lines == real_changed_lines
