import pytest
import os
import subprocess
import shutil
import sqlite3
from tests_selector.utils.db import DatabaseHelper, DB_FILE_NAME
from tests_selector.select import (
    get_tests_and_data_current,
    get_tests_and_data_committed,
)
from tests_selector.utils.common import read_newly_added_tests


@pytest.fixture(scope="session", autouse=True)
def temp_project_repo(tmpdir_factory):
    temp_folder = tmpdir_factory.mktemp("temp")
    shutil.copytree(
        "./tests_selector/tests/helper_project", str(temp_folder), dirs_exist_ok=True
    )
    os.chdir(temp_folder)

    with open(".gitignore", "w") as f:
        lines = ["*.db\n", ".coverage\n", "*__pycache__*\n"]
        for line in lines:
            f.write(line)

    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "1"])
    subprocess.run(["tests_selector_init"])
    return temp_folder


@pytest.fixture(scope="function", autouse=True)
def teardown_method():
    yield
    subprocess.run(["git", "restore", "."])
    subprocess.run(["git", "checkout", "master"])
    subprocess.run(["git", "branch", "-D", "new-branch"])
    subprocess.run(["tests_selector_init"])


class TestHelper:
    def get_mapping_id_from_filename(filename, is_srcfile):
        if is_srcfile:
            sql = "SELECT id FROM src_file WHERE path = ?"
        else:
            sql = "SELECT id from test_file WHERE path = ?"

        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        file_id = c.execute(sql, (filename,)).fetchone()[0]
        conn.close()
        return file_id

    def get_mapping_lines_for_srcfile(src_file_id):
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        lines = [
            x[0]
            for x in c.execute(
                "SELECT line_id FROM test_map WHERE file_id = ?", (src_file_id,)
            ).fetchall()
        ]
        conn.close()
        return lines

    def get_tests_from_tool_current():
        db = DatabaseHelper()
        db.init_conn()
        (
            test_set,
            _,
            _,
        ) = get_tests_and_data_current(db)
        db.close_conn()
        return test_set

    def get_tests_from_tool_committed():
        db = DatabaseHelper()
        db.init_conn()
        (
            test_set,
            _,
            _,
            _,
            _,
        ) = get_tests_and_data_committed(db)
        db.close_conn()
        return test_set

    def get_all_tests_for_srcfile(src_file_id):
        db = DatabaseHelper()
        db.init_conn()
        all_tests = db.query_all_tests_srcfile(src_file_id)
        db.close_conn()
        return all_tests

    def get_newly_added_tests_from_tool():
        db = DatabaseHelper()
        db.init_conn()
        new_tests = read_newly_added_tests(db)
        db.close_conn()
        return new_tests

    def new_test_exists_in_mapping_db(testname):
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        sql = "SELECT EXISTS(SELECT id FROM test_function WHERE context = ?)"
        exists = bool(c.execute(sql, (testname,)).fetchone()[0])
        return exists

    def change_file(change_path, file_path):
        subprocess.run(["cp", "-f", change_path, file_path])

    def commit_change(filename, message):
        subprocess.run(["git", "add", filename])
        subprocess.run(["git", "commit", "-m", message])

    def run_tool():
        subprocess.run(["tests_selector"])

    def checkout_new_branch():
        subprocess.run(["git", "checkout", "-b", "new-branch"])


@pytest.fixture
def helper():
    return TestHelper