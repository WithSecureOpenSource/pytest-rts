import ast
import os

import coverage
import pytest
from _pytest.python import Function

from tests_selector.helper import get_cursor, function_lines


class InitPhasePlugin:
    def __init__(self):
        self.test_func_lines = {}
        self.cov = coverage.Coverage()
        self.cov._warn_no_data = True
        self._should_write_debug = False
        self.cursor, self.conn = get_cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute("DROP TABLE IF EXISTS test_map")
        self.cursor.execute("DROP TABLE IF EXISTS src_file")
        self.cursor.execute("DROP TABLE IF EXISTS test_file")
        self.cursor.execute("DROP TABLE IF EXISTS test_function")
        self.cursor.execute(
            "CREATE TABLE test_map (file_id INTEGER, test_function_id INTEGER, line_id INTEGER, UNIQUE(file_id,test_function_id,line_id))"
        )
        self.cursor.execute(
            "CREATE TABLE src_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.cursor.execute(
            "CREATE TABLE test_file (id INTEGER PRIMARY KEY, path TEXT, UNIQUE (path))"
        )
        self.cursor.execute(
            """CREATE TABLE test_function (
                                id INTEGER PRIMARY KEY,
                                test_file_id INTEGER, 
                                context TEXT, 
                                start INTEGER, 
                                end INTEGER,
                                FOREIGN KEY (test_file_id) REFERENCES test_file(id), 
                                UNIQUE (context))"""
        )

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
        lines = data[3]
        testfile = testname.split("::")[0]

        func_name_no_params = func_name.split("[")[0]
        line_tuple = self.test_func_lines[testfile][func_name_no_params]

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
