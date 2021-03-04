"""This module contains code for running a specific test set with mapping database updating"""
import os

import coverage

from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import calculate_func_lines, filter_and_sort_pytest_items
from pytest_rts.pytest.mapper_plugin import MapperPlugin


def _read_testfile_functions(testfile_path):
    """Calculate test file function lines and
    expect an error for deleted test file between commits
    """
    try:
        return calculate_func_lines(coverage.python.get_python_source(testfile_path))
    except coverage.misc.NoSource:
        return {}


class UpdatePhasePlugin(MapperPlugin):
    """Class to handle running of selected tests and updating mapping with the results"""

    def __init__(self, test_set, mappinghelper, testgetter):
        """Constructor opens database connection and initializes Coverage.py"""
        super().__init__(mappinghelper)
        self.test_set = test_set
        self.testgetter = testgetter
        self.test_func_times = self.testgetter.test_function_runtimes

    def pytest_collection_modifyitems(self, session, config, items):
        """
        Sorts tests based on database duration and
        calculates test function start and end line numbers
        """
        del config
        original_length = len(items)
        items[:] = filter_and_sort_pytest_items(
            self.test_set, items, self.test_func_times
        )

        self.testfiles.update({os.path.relpath(item.location[0]) for item in items})
        self.test_func_lines = {
            testfile_path: _read_testfile_functions(testfile_path)
            for testfile_path in self.testfiles
        }

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(items)))
        )
