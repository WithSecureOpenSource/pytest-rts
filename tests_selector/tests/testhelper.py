import sqlite3
import subprocess
from tests_selector.utils.db import DatabaseHelper, DB_FILE_NAME
from tests_selector.select import (
    get_tests_and_data_current,
    get_tests_and_data_committed,
)
from tests_selector.utils.common import read_newly_added_tests


class TestHelper:
    def get_mapping_id_from_filename(filename, is_srcfile):
        if is_srcfile:
            sql = "SELECT id FROM src_file WHERE path = ?"
        else:
            sql = "SELECT id from test_file WHERE path = ?"

        conn = sqlite3.connect(DB_FILE_NAME)
        file_id = conn.execute(sql, (filename,)).fetchone()[0]
        conn.close()
        return file_id

    def get_mapping_lines_for_srcfile(src_file_id):
        conn = sqlite3.connect(DB_FILE_NAME)
        lines = [
            x[0]
            for x in conn.execute(
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
        sql = "SELECT EXISTS(SELECT id FROM test_function WHERE context = ?)"
        exists = bool(conn.execute(sql, (testname,)).fetchone()[0])
        conn.close()
        return exists

    def change_file(change_path, file_path):
        subprocess.run(["cp", "-f", change_path, file_path], check=True)

    def commit_change(filename, message):
        subprocess.run(["git", "add", filename], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)

    def run_tool():
        subprocess.run(["tests_selector"], check=True)

    def checkout_new_branch():
        subprocess.run(["git", "checkout", "-b", "new-branch"], check=True)
