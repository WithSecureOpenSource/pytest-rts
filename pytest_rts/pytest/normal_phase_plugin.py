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
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
                if item.nodeid not in self.test_func_times:
                    self.test_func_times[item.nodeid] = sys.maxsize

        items[:] = sorted(selected, key=lambda item: self.test_func_times[item.nodeid])

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )
