"""This module contains code for collecting newly added tests"""


class CollectPlugin:  # pylint: disable=too-few-public-methods
    """Plugin class for pytest"""

    def __init__(self, existing_tests):
        """Set test set that exists in database as value"""
        self.collected = []
        self.existing_tests = existing_tests

    def pytest_collection_modifyitems(self, session, config, items):
        """Select tests that have not been previously seen"""
        del session, config
        for item in items:
            if item.nodeid not in self.existing_tests:
                self.collected.append(item.nodeid)
