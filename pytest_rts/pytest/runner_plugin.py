"""This module contains code for running a specific test set"""
# pylint: disable=too-few-public-methods
from typing import List, Set

from _pytest.main import Session
from _pytest.nodes import Item

from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import filter_pytest_items


class RunnerPlugin:
    """Plugin class for pytest"""

    def __init__(self, existing_tests: Set[str], tests_from_changes: Set[str]) -> None:
        """Set existing tests"""
        self.existing_tests = existing_tests
        self.tests_from_changes = tests_from_changes

    def pytest_collection_modifyitems(
        self,
        session: Session,
        config,  # pylint: disable=unused-argument
        items: List[Item],
    ) -> None:
        """Select only specific tests for running"""
        original_length = len(items)
        items[:] = filter_pytest_items(
            items, self.existing_tests, self.tests_from_changes
        )
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(items)))
        )
