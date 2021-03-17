"""This module contains code for running a specific test set"""
# pylint: disable=too-few-public-methods
from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import filter_pytest_items


class RunnerPlugin:
    """Plugin class for pytest"""

    def __init__(self, existing_tests):
        """Set existing tests"""
        self.existing_tests = existing_tests

    def pytest_collection_modifyitems(
        self, session, config, items
    ):  # pylint: disable=unused-argument
        """Select only specific tests for running"""
        original_length = len(items)
        items[:] = filter_pytest_items(items, self.existing_tests)
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(items)))
        )
