import coverage
import pytest
from _pytest.python import Function
from timeit import default_timer as timer
from tests_selector.pytest.fake_item import FakeItem
from tests_selector.utils.common import (
    function_lines,
    calculate_func_lines,
    save_data,
)
from tests_selector.utils.db import DatabaseHelper


class UpdatePhasePlugin:
    def __init__(self, test_set):
        self.test_func_lines = {}
        self.test_func_times = {}
        self.cov = coverage.Coverage()
        self.cov._warn_unimported_source = False
        self.test_set = test_set
        self.testfiles = set()
        self.db = DatabaseHelper()
        self.db.copy_db()  # Copy mapping.db to new_mapping.db
        self.db.init_conn(True)  # Boolean to state that new_mapping.db is used
        self.fill_times_dict()

    def fill_times_dict(self):
        for testname in self.test_set:
            self.test_func_times[testname] = self.db.get_test_duration(testname)

    def pytest_collection_modifyitems(self, session, config, items):
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

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
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
