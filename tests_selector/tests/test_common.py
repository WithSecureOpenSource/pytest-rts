import ast
import pytest
from tests_selector.utils import git, common
from tests_selector.utils.db import DatabaseHelper


def test_tests_from_changed_sourcefiles(helper):
    db = DatabaseHelper()
    db.init_conn()

    helper.change_file("changes/car/change_accelerate.txt", "src/car.py")

    changed_files = ["src/car.py"]
    test_files, src_files = common.split_changes(changed_files, db)
    diff_dict = common.file_diff_dict_current(src_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
        files_to_warn,
    ) = common.tests_from_changed_srcfiles(diff_dict, src_files, db)
    db.close_conn()

    assert test_set == {"tests/test_car.py::test_acceleration"}


def test_tests_from_changed_testfiles(helper):
    db = DatabaseHelper()
    db.init_conn()

    helper.change_file(
        "changes/test_shop/change_test_normal_shop_purchase.txt",
        "tests/test_shop.py",
    )

    changed_files = [
        "tests/test_shop.py",
    ]
    test_files, src_files = common.split_changes(changed_files, db)
    diff_dict = common.file_diff_dict_current(test_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
    ) = common.tests_from_changed_testfiles(diff_dict, test_files, db)
    db.close_conn()

    assert test_set == {"tests/test_shop.py::test_normal_shop_purchase"}


def test_split_changes():
    db = DatabaseHelper()
    db.init_conn()

    change_list = ["src/car.py", "random_file.txt", "tests/test_car.py"]
    for path in change_list:
        with open(path, "w") as f:
            f.write("nothing")

    test_files, src_files = common.split_changes(change_list, db)
    db.close_conn()

    for t in test_files:
        assert t[1] in {"tests/test_car.py"}

    for s in src_files:
        assert s[1] in {"src/car.py"}


def test_newly_added_tests(helper):
    db = DatabaseHelper()
    db.init_conn()

    helper.change_file("changes/test_car/add_test_passengers.txt", "tests/test_car.py")

    new_tests = common.read_newly_added_tests(db)
    db.close_conn()

    assert new_tests == {"tests/test_car.py::test_passengers"}


def test_line_mapping(helper):
    helper.change_file("changes/car/shift_2_forward.txt", "src/car.py")

    diff = git.file_diff_data_current("src/car.py")
    lines_to_query, updates_to_lines, _ = git.get_test_lines_and_update_lines(diff)
    line_map = common.line_mapping(updates_to_lines, "src/car.py")

    expected_line_map = {
        1: 3,
        2: 4,
        3: 5,
        4: 6,
        5: 7,
        6: 8,
        7: 9,
        8: 10,
        9: 11,
        10: 12,
        11: 13,
        12: 14,
        13: 15,
        14: 16,
        15: 17,
        16: 18,
        17: 19,
        18: 20,
        19: 21,
        20: 22,
        21: 23,
        22: 24,
        23: 25,
        24: 26,
        25: 27,
    }

    assert line_map == expected_line_map


def test_function_lines():
    with open("src/car.py", "r") as f:
        code = f.read()
        codelines = f.readlines()

    parsed_code = ast.parse(code)
    func_lines = common.function_lines(parsed_code, len(codelines))

    expected_func_lines = [
        ("__init__", 4, 7),
        ("get_speed", 9, 10),
        ("accelerate", 12, 13),
        ("get_passengers", 15, 16),
        ("add_passenger", 18, 20),
        ("remove_passenger", 22, 0),
    ]

    assert func_lines == expected_func_lines
