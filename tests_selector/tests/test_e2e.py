import pytest
import os
import subprocess

from tests_selector.utils import (
    db,
    common,
    git,
)
from tests_selector import select


def test_full_integration(temp_project_repo):
    subprocess.run(["git", "checkout", "-b", "new-branch"])
    c, conn = db.get_cursor()

    # Check correct files in mapping to begin with
    test_files, src_files = db.get_testfiles_and_srcfiles()
    car_id = [x[0] for x in src_files if x[1] == "src/car.py"][0]
    src_file_names = [x[1] for x in src_files]
    test_file_names = [x[1] for x in test_files]

    assert src_file_names == ["src/car.py", "src/shop.py"]
    assert test_file_names == ["tests/test_car.py", "tests/test_some_methods.py"]

    # Add a new method to car.py
    with open("./src/car.py", "a") as f:
        f.write("\n\n")
        f.write("    def new_method():\n")
        f.write("        i = self.speed + self.seats\n")
        f.write("        return i + 8\n")

    # Get working directory diffs and test_set like in tests_selector script
    changed_files = git.changed_files_current()
    changed_test_files, changed_src_files = common.split_changes(changed_files)
    diff_dict_src = common.file_diff_dict_current(changed_src_files)
    diff_dict_test = common.file_diff_dict_current(changed_test_files)
    test_set, update_tuple = select.get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
    )
    all_tests_car = db.query_all_tests_srcfile(car_id)

    # New method addition = test_set should be all tests of that file
    assert list(test_set) == all_tests_car

    # Run tests_selector, db shouldn't update
    old_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (car_id,)
        ).fetchall()
    ]
    subprocess.run(["tests_selector"])
    new_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (car_id,)
        ).fetchall()
    ]
    assert old_car_lines == new_car_lines

    # Commit changes
    subprocess.run(["git", "add", "src/car.py"])
    subprocess.run(["git", "commit", "-m", "car_changes"])

    # Get branch comparison diffs and test_set like in tests_selector script
    changed_files = git.changed_files_branch()
    changed_test_files, changed_src_files = common.split_changes(changed_files)
    diff_dict_src = common.file_diff_dict_branch(changed_src_files)
    diff_dict_test = common.file_diff_dict_branch(changed_test_files)
    test_set, update_tuple = select.get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
    )
    # New method addition = test_set should be all tests of that file
    assert list(test_set) == all_tests_car

    # DB should update after running this
    # But no new test tests new method so lines should be the same
    subprocess.run(["tests_selector"])
    new_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (car_id,)
        ).fetchall()
    ]
    assert old_car_lines == new_car_lines

    # Add a new test method
    with open("./tests/test_car.py", "a") as f:
        f.write("\n\n")
        f.write("def test_add_passenger():\n")
        f.write("    car = Car(3,0,1)\n")
        f.write("    car.add_passenger()\n")
        f.write("    assert car.get_passengers() == 2\n")

    # Get working directory diffs and test_set like in tests_selector script
    changed_files = git.changed_files_current()
    changed_test_files, changed_src_files = common.split_changes(changed_files)
    diff_dict_src = common.file_diff_dict_current(changed_src_files)
    diff_dict_test = common.file_diff_dict_current(changed_test_files)
    test_set, update_tuple = select.get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
    )
    # Also get newly added tests
    new_tests = common.read_newly_added_tests()

    # Changes test_set should be empty
    # Newline at the end existing test might also be considered a change?
    assert list(test_set) == []
    # New test should be found
    new_test_name = "tests/test_car.py::test_add_passenger"
    assert list(new_tests) == [new_test_name]

    # Running test_selector should run tests but not add new test to database
    subprocess.run(["tests_selector"])
    new_test_db = c.execute(
        "SELECT id FROM test_function WHERE context = ?", (new_test_name,)
    ).fetchall()
    assert len(new_test_db) == 0

    # Commit changes
    subprocess.run(["git", "add", "tests/test_car.py"])
    subprocess.run(["git", "commit", "-m", "test_car_changes"])

    # Get branch comparison diffs and test_set like in tests_selector script
    changed_files = git.changed_files_branch()
    changed_test_files, changed_src_files = common.split_changes(changed_files)
    diff_dict_src = common.file_diff_dict_branch(changed_src_files)
    diff_dict_test = common.file_diff_dict_branch(changed_test_files)
    test_set, update_tuple = select.get_tests_from_changes(
        diff_dict_test, diff_dict_src, changed_test_files, changed_src_files
    )

    # Test_set should now include all tests from previous commit and this commit
    # = All tests for car because new method on car.py
    assert list(test_set) == all_tests_car
    # New tests should include the newly added test only
    new_tests = common.read_newly_added_tests()
    assert list(new_tests) == [new_test_name]

    # Running tests_selector should now update database
    # So new test function should be found in db
    subprocess.run(["tests_selector"])
    new_test_func_id = c.execute(
        "SELECT id FROM test_function WHERE context = ?", (new_test_name,)
    ).fetchone()
    assert new_test_func_id[0] != None
    new_mapping_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE test_function_id = ? AND file_id = ?",
            (new_test_func_id[0], car_id),
        ).fetchall()
    ]
    assert new_mapping_lines == [4, 5, 6, 15, 18, 19]

    subprocess.run(["git", "checkout", "master"])
    subprocess.run(["git", "branch", "-D", "new-branch"])
    subprocess.run(["tests_selector_init"])
    conn.close()


def test_db_updating_only_once(temp_project_repo):
    subprocess.run(["git", "checkout", "-b", "new-branch"])
    c, conn = db.get_cursor()
    file_id_car = c.execute(
        "SELECT id FROM src_file WHERE path = ?", ("src/car.py",)
    ).fetchone()[0]
    old_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (file_id_car,)
        ).fetchall()
    ]

    with open("./src/car.py", "r") as f:
        lines = f.readlines()
        lines[4] = lines[4] + "\n\n\n"
        lines[12] = lines[12] + "\n\n"

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    # Changes in working directory, run tests_selector
    # Shouldn't update db
    subprocess.run(["tests_selector"])
    new_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (file_id_car,)
        ).fetchall()
    ]
    assert old_car_lines == new_car_lines

    # Commit car.py changes
    subprocess.run(["git", "add", "src/car.py"])
    subprocess.run(["git", "commit", "-m", "car_changes"])

    # Committed changes, run tests_selector
    # Should update db
    subprocess.run(["tests_selector"])
    new_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (file_id_car,)
        ).fetchall()
    ]
    assert old_car_lines != new_car_lines
    assert new_car_lines == [4, 5, 9, 12, 15]

    # Run again, shouldn't update db
    subprocess.run(["tests_selector"])
    new_car_lines = [
        x[0]
        for x in c.execute(
            "SELECT line_id FROM test_map WHERE file_id = ?", (file_id_car,)
        ).fetchall()
    ]
    assert new_car_lines == [4, 5, 9, 12, 15]

    subprocess.run(["git", "checkout", "master"])
    subprocess.run(["git", "branch", "-D", "new-branch"])
    subprocess.run(["tests_selector_init"])
    conn.close()
