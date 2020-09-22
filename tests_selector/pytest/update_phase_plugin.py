import ast
import os
import coverage
import pytest
from _pytest.python import Function
from timeit import default_timer as timer
from tests_selector.pytest.fake_item import FakeItem
from tests_selector.utils.common import function_lines
from tests_selector.utils.db import (
    init_mapping_db,
    save_mapping_lines,
    save_src_file,
    save_testfile_and_func,
    get_test_duration,
)


class UpdatePhasePlugin:
    def __init__(self, test_set):
        self.test_func_lines = {}
        self.test_func_times = {}
        self.cov = coverage.Coverage()
        self.cov._warn_no_data = True
        self._should_write_debug = False
        self.test_set = test_set
        self.fill_times_dict()

    def start(self):
        self.cov.erase()
        self.cov.start()

    def stop(self):
        self.cov.stop()
        self.cov.save()

    def fill_times_dict(self):
        for testname in self.test_set:
            self.test_func_times[testname] = get_test_duration(testname)

    def calculate_func_lines(self, testfile):
        src_code = coverage.python.get_python_source(testfile)
        parsed_src_code = ast.parse(src_code)
        func_lines = function_lines(parsed_src_code, len(src_code.splitlines()))
        lower_dict = {}
        for t in func_lines:
            func = t[0]
            start = t[1]
            end = t[2]
            lower_dict[func] = (start, end)
        self.test_func_lines[testfile] = lower_dict

    def save_data(self, item, elapsed):
        testname = item.nodeid
        func_name = item.name
        testfile = testname.split("::")[0]
        func_name_no_params = func_name.split("[")[0]
        line_tuple = self.test_func_lines[testfile][func_name_no_params]
        func_start = line_tuple[0]
        func_end = line_tuple[1]
        test_file_id, test_function_id = save_testfile_and_func(
            testfile, testname, func_name, func_start, func_end, elapsed
        )
        cov_data = self.cov.get_data()
        for filename in cov_data.measured_files():
            if "tests-selector" in filename:
                continue
            src_file = os.path.relpath(filename, os.getcwd())
            src_id = save_src_file(src_file)
            save_mapping_lines(src_id, test_function_id, cov_data.lines(filename))

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
            if testfile not in self.test_func_lines:
                self.calculate_func_lines(testfile)

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        if isinstance(item, Function):
            start = timer()
            self.start()
            yield
            self.stop()
            end = timer()
            elapsed = round(end - start, 4)
            # print("duration from db:", self.test_func_times[item.nodeid])
            self.save_data(item, elapsed)
        else:
            yield
