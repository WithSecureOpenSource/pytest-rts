"""This module contains code for collecting newly added tests"""
# pylint: disable=too-few-public-methods
import sqlite3
from pytest_rts.plugin import DB_FILE_NAME
from pytest_rts.utils.testgetter import TestGetter


class CollectPlugin:
    """Plugin class for pytest to collect newly added tests"""

    def __init__(self):
        """Query existing test functions from database before collection"""
        self.collected = set()
        self.conn = sqlite3.connect(DB_FILE_NAME)
        self.testgetter = TestGetter(self.conn)
        self.existing_tests = self.testgetter.existing_tests
        self.testgetter.delete_newly_added_tests()

    def pytest_collection_modifyitems(self, session, config, items):
        """Select tests that have not been previously seen"""
        del session, config
        for item in items:
            if item.nodeid not in self.existing_tests:
                self.collected.add(item.nodeid)
        self.testgetter.set_newly_added_tests(self.collected)
        self.conn.commit()
        self.conn.close()
