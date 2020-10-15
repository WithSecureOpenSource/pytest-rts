import coverage
import pytest
from _pytest.python import Function
from timeit import default_timer as timer
from tests_selector.utils.common import (
    function_lines,
    calculate_func_lines,
    save_data,
)
from tests_selector.utils.git import get_current_head_hash
from tests_selector.utils.db import DatabaseHelper


class InitPhasePlugin:
    """Class to handle mapping database initialization"""

    def __init__(self):
        """"Constructor calls database and Coverage.py initialization"""
        self.test_func_lines = {}
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.testfiles = set()
        self.db = DatabaseHelper()
        self.db.init_conn()
        self.db.init_mapping_db()
        self.head_hash = get_current_head_hash()
        self.db.save_last_update_hash(self.head_hash)

    def pytest_collection_modifyitems(self, session, config, items):
        """Calculate function start and end line numbers from testfiles"""
        for item in items:
            testfile = item.nodeid.split("::")[0]
            self.testfiles.add(testfile)
            if testfile not in self.test_func_lines:
                testfile_src_code = coverage.python.get_python_source(testfile)
                self.test_func_lines[testfile] = calculate_func_lines(testfile_src_code)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        """Start coverage collection for each test function run and save data"""
        if isinstance(item, Function):
            start = timer()
            self.cov.erase()
            self.cov.start()
            yield
            self.cov.stop()
            self.cov.save()
            end = timer()
            elapsed = round(end - start, 4)
            save_data(
                item,
                elapsed,
                self.test_func_lines,
                self.cov.get_data(),
                self.testfiles,
                self.db,
            )
        else:
            yield
