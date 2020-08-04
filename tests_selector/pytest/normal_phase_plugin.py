import ast
import os

import coverage
import pytest
from _pytest.python import Function

from tests_selector.helper import get_cursor, function_lines
from tests_selector.pytest.fake_item import FakeItem


class NormalPhasePlugin:
    def __init__(self, test_set):
        self.test_func_lines = {}
        self.cov = coverage.Coverage()
        self.cov._warn_no_data = True
        self._should_write_debug = False
        self.cursor, self.conn = get_cursor()
        self.test_set = test_set

    def start(self):
        self.cov.erase()
        self.cov.start()

    def stop(self):
        self.cov.stop()
        self.cov.save()

    def save_data(self, item):
        testname = item.nodeid
        func_name = item.name
        cov_data = self.cov.get_data()
        for filename in cov_data.measured_files():
            self.insert_to_db((filename, testname, func_name, cov_data.lines(filename)))

    def insert_to_db(self, data):
        src_file_full = data[0]
        src_file = os.path.relpath(src_file_full, os.getcwd())
        testname = data[1]
        func_name = data[2]
        lines = data[2]
        testfile = testname.split("::")[0]

        for test_func in self.test_func_lines[testfile].keys():
            if test_func == func_name[: len(test_func)]:
                line_tuple = self.test_func_lines[testfile][test_func]
                break

        self.cursor.execute(
            "INSERT OR IGNORE INTO src_file (path) VALUES (?)", (src_file,)
        )
        src_id = self.cursor.execute(
            "SELECT id FROM src_file WHERE path == ?", (src_file,)
        ).fetchone()[0]

        self.cursor.execute(
            "INSERT OR IGNORE INTO test_file (path) VALUES (?)", (testfile,)
        )
        test_file_id = self.cursor.execute(
            "SELECT id FROM test_file WHERE path == ?", (testfile,)
        ).fetchone()[0]

        self.cursor.execute(
            "INSERT OR IGNORE INTO test_function (test_file_id,context,start,end) VALUES (?,?,?,?)",
            (test_file_id, testname, line_tuple[0], line_tuple[1]),
        )
        test_function_id = self.cursor.execute(
            "SELECT id FROM test_function WHERE context == ?", (testname,)
        ).fetchone()[0]

        for l in lines:
            self.cursor.execute(
                "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
                (src_id, test_function_id, l),
            )

    def pytest_collection_modifyitems(self, session, config, items):
        original_length = len(items)
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
        items[:] = selected
        for item in items:
            testfile = item.nodeid.split("::")[0]
            if testfile not in self.test_func_lines:
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
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        if isinstance(item, Function):
            self.start()
            yield
            self.stop()
            self.save_data(item)
        else:
            yield

    def pytest_sessionfinish(self, session):
        self.conn.commit()
        self.conn.close()
