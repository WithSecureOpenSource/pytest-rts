import ast
import pytest
import subprocess
from tests_selector.utils import git, common
from tests_selector.utils.db import DatabaseHelper


@pytest.mark.parametrize(
    "change, src_file_name, expected",
    [
        (
            "changes/car/change_accelerate.txt",
            "src/car.py",
            {"tests/test_car.py::test_acceleration"},
        ),
    ],
)
def test_tests_from_changed_sourcefiles(change, src_file_name, expected):
    db = DatabaseHelper()
    db.init_conn()

    subprocess.run(["cp", "-f", change, src_file_name])

    changed_files = [src_file_name]
    test_files, src_files = common.split_changes(changed_files, db)
    diff_dict = common.file_diff_dict_current(src_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
    ) = common.tests_from_changed_srcfiles(diff_dict, src_files, db)
    db.close_conn()

    assert test_set == expected


@pytest.mark.parametrize(
    "change, testfile_name, expected",
    [
        (
            "changes/test_shop/change_test_normal_shop_purchase.txt",
            "tests/test_some_methods.py",
            {"tests/test_some_methods.py::test_normal_shop_purchase"},
        ),
    ],
)
def test_tests_from_changed_testfiles(change, testfile_name, expected):
    db = DatabaseHelper()
    db.init_conn()

    subprocess.run(["cp", "-f", change, testfile_name])

    changed_files = [testfile_name]
    test_files, src_files = common.split_changes(changed_files, db)
    diff_dict = common.file_diff_dict_current(test_files)

    (
        test_set,
        changed_lines_dict,
        new_line_map_dict,
    ) = common.tests_from_changed_testfiles(diff_dict, test_files, db)
    db.close_conn()

    assert test_set == expected


@pytest.mark.parametrize(
    "change_list, expected_src_names, expected_test_names",
    [
        (
            ["src/car.py", "random_file.txt", "tests/test_car.py"],
            {"src/car.py"},
            {"tests/test_car.py"},
        ),
    ],
)
def test_split_changes(change_list, expected_src_names, expected_test_names):
    db = DatabaseHelper()
    db.init_conn()

    for path in change_list:
        with open(path, "w") as f:
            f.write("nothing")

    test_files, src_files = common.split_changes(change_list, db)
    db.close_conn()

    for t in test_files:
        assert t[1] in expected_test_names

    for s in src_files:
        assert s[1] in expected_src_names


@pytest.mark.parametrize(
    "change, testfile_name, expected",
    [
        (
            "changes/test_car/add_test_passengers.txt",
            "tests/test_car.py",
            {"tests/test_car.py::test_passengers"},
        ),
    ],
)
def test_newly_added_tests(change, testfile_name, expected):
    db = DatabaseHelper()
    db.init_conn()

    subprocess.run(["cp", "-f", change, testfile_name])

    new_tests = common.read_newly_added_tests(db)
    db.close_conn()

    assert new_tests == expected


@pytest.mark.parametrize(
    "change, filename, expected",
    [
        (
            "changes/car/shift_2_forward.txt",
            "src/car.py",
            {
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
            },
        ),
    ],
)
def test_line_mapping(change, filename, expected):
    subprocess.run(["cp", "-f", change, filename])

    diff = git.file_diff_data_current(filename)
    lines_to_query, updates_to_lines, _ = git.get_test_lines_and_update_lines(diff)
    line_map = common.line_mapping(updates_to_lines, filename)

    assert line_map == expected


@pytest.mark.parametrize(
    "filename, expected",
    [
        (
            "src/car.py",
            [
                ("__init__", 4, 7),
                ("get_speed", 9, 10),
                ("accelerate", 12, 13),
                ("get_passengers", 15, 16),
                ("add_passenger", 18, 20),
                ("remove_passenger", 22, 0),
            ],
        ),
    ],
)
def test_function_lines(filename, expected):
    with open(filename, "r") as f:
        code = f.read()
        codelines = f.readlines()

    parsed_code = ast.parse(code)
    func_lines = common.function_lines(parsed_code, len(codelines))

    assert func_lines == expected