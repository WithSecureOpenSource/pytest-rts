"""This module contains code for initializing the mapping database"""
from timeit import default_timer as timer
import coverage
import pytest
from _pytest.python import Function
from pytest_rts.utils.common import (
    calculate_func_lines,
    save_mapping_data,
    save_testfile_and_func_data,
)
from pytest_rts.utils.git import get_current_head_hash
from pytest_rts.utils.db import DatabaseHelper


class InitPhasePlugin:
    """Class to handle mapping database initialization"""

    def __init__(self):
        """"Constructor calls database and Coverage.py initialization"""
        self.test_func_lines = {}
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.testfiles = set()
        self.database = DatabaseHelper()
        self.database.init_conn()
        self.database.init_mapping_db()
        self.head_hash = get_current_head_hash()
        self.database.save_last_update_hash(self.head_hash)

    def pytest_collection_modifyitems(self, session, config, items):
        """Calculate function start and end line numbers from testfiles"""
        del session, config
        for item in items:
            testfile = item.nodeid.split("::")[0]
            self.testfiles.add(testfile)
            if testfile not in self.test_func_lines:
                testfile_src_code = coverage.python.get_python_source(testfile)
                self.test_func_lines[testfile] = calculate_func_lines(testfile_src_code)

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
