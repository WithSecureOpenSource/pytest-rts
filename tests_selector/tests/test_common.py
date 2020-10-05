import os
import ast

from tests_selector.utils import git, common
from tests_selector.utils.db import DatabaseHelper

def test_tests_from_changed_sourcefiles():
    db = DatabaseHelper()
    db.init_conn()

    with open("./src/car.py", "r") as f:
        lines = f.readlines()
        code = lines[11]
        lines[11] = code.strip() + "+1\n"  # change 'acceleration' func

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    changed_files = git.changed_files_current()
    test_files, src_files = common.split_changes(changed_files, db)
    src_file_id = src_files[0][0]
    diff_dict = common.file_diff_dict_current(src_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
    ) = common.tests_from_changed_srcfiles(diff_dict, src_files, db)

    assert test_set == {"tests/test_car.py::test_acceleration"}
    assert changed_lines_dict == {src_file_id: [12]}
    assert new_line_map_dict == {src_file_id: {}}
    db.close_conn()


def test_tests_from_changed_testfiles():
    db = DatabaseHelper()
    db.init_conn()
    with open("./tests/test_some_methods.py", "r") as f:
        lines = f.readlines()
        lines[8] = "\n"  # change 'test_normal_shop_purchase' test func

    with open("./tests/test_some_methods.py", "w") as f:
        for line in lines:
            f.write(line)

    changed_files = git.changed_files_current()
    test_files, src_files = common.split_changes(changed_files, db)
    test_file_id = test_files[0][0]
    diff_dict = common.file_diff_dict_current(test_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
    ) = common.tests_from_changed_testfiles(diff_dict, test_files, db)

    assert test_set == {"tests/test_some_methods.py::test_normal_shop_purchase"}
    assert changed_lines_dict == {test_file_id: [9]}
    assert new_line_map_dict == {test_file_id: {}}
    db.close_conn()


def test_split_changes():
    db = DatabaseHelper()
    db.init_conn()

    with open("./tests/test_some_methods.py", "w") as f:
        f.write("nothing")

    with open("./src/car.py", "w") as f:
        f.write("nothing")

    with open("./random_file.txt", "w") as f:
        f.write("nothing")

    changed_files = git.changed_files_current()
    test_files, src_files = common.split_changes(changed_files, db)

    assert len(test_files) == 1
    assert test_files[0][1] == "tests/test_some_methods.py"
    assert len(src_files) == 1
    assert src_files[0][1] == "src/car.py"
    os.remove("./random_file.txt")
    db.close_conn()


def test_newly_added_tests():
    db = DatabaseHelper()
    db.init_conn()
    with open("./tests/test_new_methods.py", "w") as f:
        lines = [
            "import pytest\n",
            "\n",
            "def test_new_stuff():\n",
            "    assert 1 == 1\n",
        ]
        for line in lines:
            f.write(line)

    new_tests = common.read_newly_added_tests(db)
    assert new_tests == {"tests/test_new_methods.py::test_new_stuff"}
    os.remove("./tests/test_new_methods.py")
    db.close_conn()


def test_line_mapping():
    with open("./src/car.py", "r") as f:
        lines = f.readlines()
        lines[4] = lines[4] + "\n\n\n"
        lines[12] = lines[12] + "\n\n"
        lines[19] = " "

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    diff = git.file_diff_data_current("src/car.py", ".")
    lines_to_query, updates_to_lines = git.get_test_lines_and_update_lines(diff)
    line_map = common.line_mapping(updates_to_lines, "src/car.py", ".")

    real_lines = {
        6: 9,
        7: 10,
        8: 11,
        9: 12,
        10: 13,
        11: 14,
        12: 15,
        13: 16,
        14: 19,
        15: 20,
        16: 21,
        17: 22,
        18: 23,
        19: 24,
        20: 25,
        21: 25,
        22: 26,
        23: 27,
        24: 28,
        25: 29,
        26: 30,
        27: 31,
    }

    assert line_map == real_lines


def test_function_lines():
    with open("./src/car.py", "r") as f:
        code = f.read()
        codelines = f.readlines()

    parsed_code = ast.parse(code)
    func_lines = common.function_lines(parsed_code, len(codelines))
    real_func_lines = [
        ("__init__", 4, 7),
        ("get_speed", 9, 10),
        ("accelerate", 12, 13),
        ("get_passengers", 15, 16),
        ("add_passenger", 18, 20),
        ("remove_passenger", 22, 0),
    ]

    assert len(func_lines) == 6
    assert func_lines == real_func_lines