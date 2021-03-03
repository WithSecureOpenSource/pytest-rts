"""This module contains code for running a specific test set without mapping database updating"""
# pylint: disable=too-few-public-methods
from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import filter_and_sort_pytest_items


class NormalPhasePlugin:
    """Plugin class for pytest"""

    def __init__(self, test_set, testgetter):
        """Initialize database connection"""
        self.test_set = test_set
        self.testgetter = testgetter
        self.test_func_times = self.testgetter.test_function_runtimes

    def pytest_collection_modifyitems(self, session, config, items):
        """Select only specific tests for running and prioritize them based on queried times"""
        del config
        original_length = len(items)
        items[:] = filter_and_sort_pytest_items(
            self.test_set, items, self.test_func_times
        )
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(items)))
        )
