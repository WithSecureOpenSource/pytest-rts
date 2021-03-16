"""This module contains code for running a specific test set"""
# pylint: disable=too-few-public-methods
from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import filter_and_sort_pytest_items


class RunPhasePlugin:
    """Plugin class for pytest"""

    def __init__(self, selected_test_set, existing_tests):
        """Set Coverage.py object placeholder to None"""
        self.cov = None
        self.selected_test_set = selected_test_set
        self.existing_tests = existing_tests

    def pytest_collection_modifyitems(self, session, config, items):
        """Select only specific tests for running"""
        self.cov = config.pluginmanager.getplugin("_cov").cov_controller.cov
        original_length = len(items)
        items[:] = filter_and_sort_pytest_items(
            self.selected_test_set, items, self.existing_tests
        )
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(items)))
        )

    def pytest_runtest_logstart(self, nodeid, location):
        """Switch test function name in Coverage.py when a test starts running"""
        self.cov.switch_context(nodeid)
