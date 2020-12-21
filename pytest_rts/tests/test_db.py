import sqlite3
import pytest
from pytest_rts.utils.db import DatabaseHelper, DB_FILE_NAME


def test_delete_ran_lines():
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    db = DatabaseHelper()
    db.init_conn()
    db.delete_ran_lines(old_line_ids, file_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert not new_line_ids


def test_update_db_from_src_mapping():
    # shift all lines and compare old and new lines in db
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    file_id = 1
    sql = "SELECT line_id FROM test_map WHERE file_id = ?"
    old_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    shift = 5
    line_map = {x: x + shift for x in old_line_ids}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_src_mapping(line_map, file_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_line_ids = [x[0] for x in c.execute(sql, (file_id,)).fetchall()]
    conn.close()

    assert new_line_ids == [k + shift for k in old_line_ids]


def test_update_db_from_test_mapping():
    # shift all lines and compare old and new lines in db
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    testfile_id = 2
    funclines_sql = "SELECT id,start,end FROM test_function WHERE test_file_id = ?"
    filename_sql = "SELECT path FROM test_file WHERE id = ?"

    testfile_name = c.execute(filename_sql, (testfile_id,)).fetchone()[0]
    old_func_line_dict = {
        x[0]: (x[1], x[2]) for x in c.execute(funclines_sql, (testfile_id,)).fetchall()
    }

    conn.close()

    shift = 5
    line_count = sum(1 for line in open(testfile_name))
    line_map = {x: x + shift for x in range(1, line_count + 1)}

    db = DatabaseHelper()
    db.init_conn()
    db.update_db_from_test_mapping(line_map, testfile_id)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_func_line_dict = {
        x[0]: (x[1], x[2]) for x in c.execute(funclines_sql, (testfile_id,)).fetchall()
    }
    conn.close()

    assert len(old_func_line_dict) == len(new_func_line_dict)
    for key in old_func_line_dict.keys():
        old_func_linenumbers = old_func_line_dict[key]
        new_func_linenumbers = new_func_line_dict[key]
        assert old_func_linenumbers[0] + shift == new_func_linenumbers[0]
        assert old_func_linenumbers[1] + shift == new_func_linenumbers[1]


def test_add_new_tests():
    new_tests = {"tests/test_car.py::test_acceleration"}

    db = DatabaseHelper()
    db.init_conn()
    db.add_new_tests(new_tests)
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_tests_in_db = {
        x[0] for x in c.execute("SELECT context FROM new_tests").fetchall()
    }
    conn.close()

    assert new_tests == new_tests_in_db


def test_existing_tests():
    db = DatabaseHelper()
    db.init_conn()
    existing_tests = db.existing_tests
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    all_tests_in_db = {
        x[0] for x in c.execute("SELECT context FROM test_function").fetchall()
    }
    conn.close()

    assert existing_tests == all_tests_in_db


def test_clear_new_tests():
    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO new_tests (context) VALUES ('tests/test_car.py::test_acceleration')"
    )
    conn.close()

    db = DatabaseHelper()
    db.init_conn()
    db.clear_new_tests()
    db.close_conn()

    conn = sqlite3.connect(DB_FILE_NAME)
    c = conn.cursor()
    new_tests_in_db = {
        x[0] for x in c.execute("SELECT context FROM new_tests").fetchall()
    }
    conn.close()

    assert not new_tests_in_db
