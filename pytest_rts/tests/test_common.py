import ast
import pytest
from pytest_rts.utils import git, common


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
