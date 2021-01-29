"""This module contains code for initializing the mapping database"""
import os
from timeit import default_timer as timer

import coverage
import pytest
from _pytest.python import Function

from pytest_rts.utils.common import calculate_func_lines
from pytest_rts.utils.git import get_current_head_hash
from pytest_rts.utils.mappinghelper import TestrunData


class InitPhasePlugin:
    """Class to handle mapping database initialization"""

    def __init__(self, mappinghelper):
        """"Constructor calls database and Coverage.py initialization"""
        self.cov = coverage.Coverage(data_file=None)
        self.cov._warn_unimported_source = False
        self.testfiles = None
        self.test_func_lines = None

        self.mappinghelper = mappinghelper
        self.mappinghelper.init_mapping()
        self.mappinghelper.set_last_update_hash(get_current_head_hash())

    def pytest_collection_modifyitems(self, session, config, items):
        """Calculate function start and end line numbers from testfiles"""
        del session, config
        self.testfiles = {os.path.relpath(item.location[0]) for item in items}
        self.test_func_lines = {
            testfile_path: calculate_func_lines(
                coverage.python.get_python_source(testfile_path)
            )
            for testfile_path in self.testfiles
        }

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
