"""This module contains code for running a specific test set without mapping database updating"""
# pylint: disable=too-few-public-methods
import sys

from pytest_rts.pytest.fake_item import FakeItem


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
        selected = list(filter(lambda item: item.nodeid in self.test_set, items))
        updated_runtimes = {
            item.nodeid: self.test_func_times[item.nodeid]
            if item.nodeid in self.test_func_times
            else sys.maxsize
            for item in selected
        }

        items[:] = sorted(selected, key=lambda item: updated_runtimes[item.nodeid])

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )
