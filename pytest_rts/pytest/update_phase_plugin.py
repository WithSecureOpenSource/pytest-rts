"""This module contains code for running a specific test set with mapping database updating"""
from timeit import default_timer as timer
import coverage
import pytest
from _pytest.python import Function
from pytest_rts.utils.db import DatabaseHelper
from pytest_rts.pytest.fake_item import FakeItem
from pytest_rts.utils.common import (
    calculate_func_lines,
    save_mapping_data,
    save_testfile_and_func_data,
)


class UpdatePhasePlugin:
    """Class to handle running of selected tests and updating mapping with the results"""

    def __init__(self, test_set):
        """Constructor opens database connection and initializes Coverage.py"""
        self.test_func_lines = {}
        self.test_func_times = {}
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.test_set = test_set
        self.testfiles = set()
        self.database = DatabaseHelper()
        self.database.init_conn()
        self.fill_times_dict()

    def fill_times_dict(self):
        """Gets test durations from database used for test prioritization"""
        for testname in self.test_set:
            self.test_func_times[testname] = self.database.get_test_duration(testname)

    def add_missing_testfiles(self):
        """Checks database for testfile names
        to prevent them for getting mapped to source code files
        """
        db_test_files, _ = self.database.get_testfiles_and_srcfiles()
        for testfile in db_test_files:
            filename = testfile[1]
            self.testfiles.add(filename)

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
        # sort tests based on duration value from database
        items[:] = sorted(selected, key=lambda item: self.test_func_times[item.nodeid])

        for item in items:
            testfile = item.nodeid.split("::")[0]
            self.testfiles.add(testfile)
            if testfile not in self.test_func_lines:
                testfile_src_code = coverage.python.get_python_source(testfile)
                self.test_func_lines[testfile] = calculate_func_lines(testfile_src_code)

        self.add_missing_testfiles()

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
            self.cov.save()
            end = timer()
            elapsed = round(end - start, 4)
            _, test_function_id = save_testfile_and_func_data(
                item, elapsed, self.test_func_lines, self.database
            )
            save_mapping_data(
                test_function_id,
                self.cov.get_data(),
                self.testfiles,
                self.database,
            )
        else:
            yield
