"""This module contains code for running a specific test set without mapping database updating"""
from pytest_rts.utils.db import DatabaseHelper
from pytest_rts.pytest.fake_item import FakeItem


class NormalPhasePlugin:
    """Plugin class for pytest"""

    def __init__(self, test_set):
        """Initialize database connection"""
        self.test_func_times = {}
        self.test_set = test_set
        self.database = DatabaseHelper()
        self.database.init_conn()
        self.fill_times_dict()

    def fill_times_dict(self):
        """Query running times of tests from database"""
        for testname in self.test_set:
            self.test_func_times[testname] = self.database.get_test_duration(testname)

    def pytest_collection_modifyitems(self, session, config, items):
        """Select only specific tests for running and prioritize them based on queried times"""
        del config
        original_length = len(items)
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)

        items[:] = sorted(selected, key=lambda item: self.test_func_times[item.nodeid])

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )
