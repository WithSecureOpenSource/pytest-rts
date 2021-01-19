"""This module contains code for running a specific test set with mapping database updating"""
import sys
from timeit import default_timer as timer
import coverage
import pytest
from _pytest.python import Function
from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import calculate_func_lines
from pytest_rts.utils.mappinghelper import TestrunData


class UpdatePhasePlugin:
    """Class to handle running of selected tests and updating mapping with the results"""

    def __init__(self, test_set, mappinghelper, testgetter):
        """Constructor opens database connection and initializes Coverage.py"""
        self.test_func_lines = {}
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.test_set = test_set

        self.mappinghelper = mappinghelper
        self.testgetter = testgetter

        self.testfiles = set(self.mappinghelper.testfiles)
        self.test_func_times = self.testgetter.test_function_runtimes

    def pytest_collection_modifyitems(self, session, config, items):
        """
        Sorts tests based on database duration and
        calculates test function start and end line numbers
        """
        del config
        original_length = len(items)
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
                if item.nodeid not in self.test_func_times:
                    self.test_func_times[item.nodeid] = sys.maxsize
        # sort tests based on duration value from database
        items[:] = sorted(selected, key=lambda item: self.test_func_times[item.nodeid])

        for item in items:
            testfile = item.nodeid.split("::")[0]
            self.testfiles.add(testfile)
            if testfile not in self.test_func_lines:
                testfile_src_code = coverage.python.get_python_source(testfile)
                self.test_func_lines[testfile] = calculate_func_lines(testfile_src_code)

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
