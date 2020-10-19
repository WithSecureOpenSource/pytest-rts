import subprocess
import sqlite3
import pytest
from tests_selector.utils.common import read_newly_added_tests
from tests_selector.utils.db import DatabaseHelper, DB_FILE_NAME
from tests_selector.select import (
    get_tests_and_data_current,
    get_tests_and_data_committed,
)


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


@pytest.mark.parametrize(
    "new_method_srcfile, new_method_testfile",
    [
        (
            ("changes/car/add_new_method.txt", "src/car.py"),
            (
                "changes/test_car/add_test_passengers.txt",
                "tests/test_car.py",
                "tests/test_car.py::test_passengers",
            ),
        ),
    ],
)
def test_full_integration(new_method_srcfile, new_method_testfile):
    subprocess.run(["git", "checkout", "-b", "new-branch"])

    change_for_new_src_method = new_method_srcfile[0]
    filename_for_new_src_method = new_method_srcfile[1]
    src_file_id = get_mapping_id_from_filename(
        filename_for_new_src_method, is_srcfile=True
    )

    change_for_new_test = new_method_testfile[0]
    filename_for_new_test = new_method_testfile[1]
    new_test_name = new_method_testfile[2]

    # Add a new method to source file
    subprocess.run(["cp", "-f", change_for_new_src_method, filename_for_new_src_method])

    all_tests_srcfile = get_all_tests_for_srcfile(src_file_id)
    # Get working directory test_set like in tests_selector script
    workdir_test_set = get_tests_from_tool_current()

    # New method addition = test_set should be all tests of that file
    assert workdir_test_set == set(all_tests_srcfile)

    # Run tests_selector, db shouldn't update
    old_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)
    subprocess.run(["tests_selector"])
    new_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)

    assert old_srcfile_lines == new_srcfile_lines

    # Commit changes
    subprocess.run(["git", "add", filename_for_new_src_method])
    subprocess.run(["git", "commit", "-m", "new_method_src"])

    # Get committed changes test_set like in tests_selector script
    commit_test_set = get_tests_from_tool_committed()

    # New method addition = test_set should be all tests of that file
    assert commit_test_set == set(all_tests_srcfile)

    # DB should update after running test selector
    # But no new test tests new method so lines should be the same
    subprocess.run(["tests_selector"])
    new_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_srcfile_lines == new_srcfile_lines

    # Add a new test method
    subprocess.run(["cp", "-f", change_for_new_test, filename_for_new_test])

    # Get working directory diffs and test_set like in tests_selector script
    workdir_test_set2 = get_tests_from_tool_current()
    # Changes test_set should be empty
    # But newline at the end existing test is also considered a change
    assert workdir_test_set2 == set()

    # Running test_selector should not add new test to database
    subprocess.run(["tests_selector"])
    assert not new_test_exists_in_mapping_db(new_test_name)

    # Commit changes
    subprocess.run(["git", "add", filename_for_new_test])
    subprocess.run(["git", "commit", "-m", "new_test_method"])

    # Get committed changes test_set like in tests_selector script
    commit_test_set2 = get_tests_from_tool_committed()

    # Test_set should now include all tests from changes between this commit and previous
    # = New test method + newline causing acceleration test to show up
    assert commit_test_set2 == {new_test_name}

    # New tests should include the newly added test only
    new_tests = get_newly_added_tests_from_tool()
    assert new_tests == {new_test_name}

    # Running tests_selector should now update database = new test function should be found in db
    subprocess.run(["tests_selector"])
    assert new_test_exists_in_mapping_db(new_test_name)


@pytest.mark.parametrize(
    "change, new_mapping, filename",
    [("changes/car/shift_2_forward.txt", [6, 7, 8, 11, 14], "src/car.py")],
)
def test_db_updating_only_once(change, new_mapping, filename):
    subprocess.run(["git", "checkout", "-b", "new-branch"])

    src_file_id = get_mapping_id_from_filename(filename, is_srcfile=True)
    old_lines = get_mapping_lines_for_srcfile(src_file_id)

    # Change src file
    subprocess.run(["cp", "-f", change, filename])

    # Changes in working directory, run tests_selector
    # Shouldn't update db
    subprocess.run(["tests_selector"])
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines == new_lines

    # Commit changes
    subprocess.run(["git", "add", filename])
    subprocess.run(["git", "commit", "-m", "change1"])

    # Committed changes, run tests_selector
    # Should update db
    subprocess.run(["tests_selector"])
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines != new_lines
    assert new_lines == new_mapping

    # Run again, shouldn't update db
    subprocess.run(["tests_selector"])
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert new_lines == new_mapping
