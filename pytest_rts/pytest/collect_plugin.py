"""This module contains code for collecting newly added tests"""
# pylint: disable=too-few-public-methods
from pytest_rts.utils.db import DatabaseHelper


class CollectPlugin:
    """Plugin class for pytest to collect newly added tests"""

    def __init__(self):
        """Query existing test functions from database before collection"""
        self.collected = set()
        self.database = DatabaseHelper()
        self.database.init_conn()
        self.existing_tests = self.database.get_existing_tests()
        self.database.clear_new_tests()

    def pytest_collection_modifyitems(self, session, config, items):
        """Select tests that have not been previously seen"""
        del session, config
        for item in items:
            if item.nodeid not in self.existing_tests:
                self.collected.add(item.nodeid)
        self.database.add_new_tests(self.collected)
