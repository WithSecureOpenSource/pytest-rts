"""This module contains code for capturing pytest exit code for running a test set"""


class CaptureSpecificPlugin:  # pylint: disable=too-few-public-methods
    """Plugin class for pytest"""

    def __init__(self, test_set):
        """Set test set as a value"""
        self.test_set = test_set

    def pytest_collection_modifyitems(self, session, config, items):
        """Only select specific tests for running"""
        del session, config
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
        items[:] = selected
