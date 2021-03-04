"""This module contains fuctions for test selecting operations"""
import ast
import os
import subprocess
import sys
from typing import Dict, List, Tuple

from _pytest.nodes import Item

from pytest_rts.connection import MappingConn
from pytest_rts.utils.git import (
    file_diff_data_between_commits,
    file_diff_data_current,
)


def file_diff_dict_current(files) -> Dict[int, str]:
    """Returns a dictionary with file id as key and git diff as value"""
    return {file_id: file_diff_data_current(filename) for file_id, filename in files}


def file_diff_dict_between_commits(files, commithash1, commithash2) -> Dict[int, str]:
    """Returns a dictionary with file id as key and git diff as value"""
    return {
        file_id: file_diff_data_between_commits(filename, commithash1, commithash2)
        for file_id, filename in files
    }


def run_new_test_collection():
    """Run collect plugin with the same connection string"""
    subprocess.run(["pytest_rts_collect", MappingConn.connection_string], check=True)


def line_mapping(updates_to_lines, filename, project_folder=".") -> Dict[int, int]:
    """Calculate new line numbers from given changes"""
    try:
        with open(os.path.join(".", project_folder, filename)) as filetoread:
            line_count = len(filetoread.readlines())
    except OSError:
        return {}
    new_line_mapping = {}
    for i, _ in enumerate(updates_to_lines):
        if i + 1 >= len(updates_to_lines):
            next_point = line_count
        else:
            next_point = updates_to_lines[i + 1][0]

        current = updates_to_lines[i][0]
        diff = updates_to_lines[i][1]

        if diff == 0:
            continue
        for k in range(current + 1, next_point + 1):
            new_line_mapping[k] = k + diff

    return new_line_mapping


def function_lines(node, end):
    """Calculate start and end line numbers for python functions"""

    def _next_lineno(i, end):
        try:
            return node[i + 1].decorator_list[0].lineno - 1
        except (IndexError, AttributeError):
            pass

        try:
            return node[i + 1].lineno - 1
        except IndexError:
            return end
        except AttributeError:
            return None

    result = []

    if isinstance(node, ast.AST):
        if (
            node.__class__.__name__ == "FunctionDef"
            or node.__class__.__name__ == "AsyncFunctionDef"
        ):
            result.append((node.name, node.body[0].lineno, end))

        for _, field_value in ast.iter_fields(node):
            result.extend(function_lines(field_value, end))

    elif isinstance(node, list):
        for i, item in enumerate(node):
            result.extend(function_lines(item, _next_lineno(i, end)))

    return result


def calculate_func_lines(src_code) -> Dict[str, Tuple[int, int]]:
    """Calculate start and end line numbers for all functions in given code string"""
    parsed_src_code = ast.parse(src_code)
    func_lines = function_lines(parsed_src_code, len(src_code.splitlines()))
    return {x[0]: (x[1], x[2]) for x in func_lines}


def filter_and_sort_pytest_items(test_set, pytest_items, runtimes) -> List[Item]:
    """Selected pytest items based on found tests
    ordered by their runtimes
    """
    selected = filter(lambda item: item.nodeid in test_set, pytest_items)
    return sorted(
        selected,
        key=lambda item: runtimes[item.nodeid]
        if item.nodeid in runtimes and runtimes[item.nodeid]
        else sys.maxsize,
    )
