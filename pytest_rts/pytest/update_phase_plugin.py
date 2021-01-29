"""This module contains code for running a specific test set with mapping database updating"""
import os
import sys
from timeit import default_timer as timer

import coverage
import pytest
from _pytest.python import Function

from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import calculate_func_lines
from pytest_rts.utils.mappinghelper import TestrunData


def _read_testfile_functions(testfile_path):
    """Calculate test file function lines and
    expect an error for deleted test file between commits
    """
    try:
        return calculate_func_lines(coverage.python.get_python_source(testfile_path))
    except coverage.misc.NoSource:
        return {}


class UpdatePhasePlugin:
    """Class to handle running of selected tests and updating mapping with the results"""

    def __init__(self, test_set, mappinghelper, testgetter):
        """Constructor opens database connection and initializes Coverage.py"""
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.test_set = test_set

        self.mappinghelper = mappinghelper
        self.testgetter = testgetter

        self.testfiles = {testfile[1] for testfile in self.mappinghelper.testfiles}
        self.test_func_lines = None
        self.test_func_times = self.testgetter.test_function_runtimes

    def pytest_collection_modifyitems(self, session, config, items):
        """
        Sorts tests based on database duration and
        calculates test function start and end line numbers
        """
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

        self.testfiles.update({os.path.relpath(item.location[0]) for item in items})
        self.test_func_lines = {
            testfile_path: _read_testfile_functions(testfile_path)
            for testfile_path in self.testfiles
        }

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        """Start coverage collection for each test function run and save data"""
        del nextitem
        if isinstance(item, Function):
            start = timer()
            self.cov.erase()
            self.cov.start()
            yield
            self.cov.stop()
            end = timer()
            elapsed = round(end - start, 4)

            testrun_data = TestrunData(
                pytest_item=item,
                elapsed_time=elapsed,
                coverage_data=self.cov.get_data(),
                found_testfiles=self.testfiles,
                test_function_lines=self.test_func_lines,
            )
            self.mappinghelper.save_testrun_data(testrun_data)
        else:
            yield
