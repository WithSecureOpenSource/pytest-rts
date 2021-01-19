"""This module contains fuctions for test selecting operations"""
import ast
import os
import subprocess
from pytest_rts.utils.git import (
    file_diff_data_between_commits,
    file_diff_data_current,
    get_test_lines_and_update_lines,
)


def file_diff_dict_current(files):
    """Returns a dictionary with file id as key and git diff as value"""
    return {file_id: file_diff_data_current(filename) for file_id, filename in files}


def file_diff_dict_between_commits(files, commithash1, commithash2):
    """Returns a dictionary with file id as key and git diff as value"""
    return {
        file_id: file_diff_data_between_commits(filename, commithash1, commithash2)
        for file_id, filename in files
    }


def tests_from_changed_testfiles(diff_dict, files, testgetter):
    """Calculate test set and update data from changes to a testfile"""

    test_set = set()
    changed_lines_map = {}
    new_line_map = {}
    for testfile in files:
        file_id = testfile[0]
        filename = testfile[1]
        changed_lines, updates_to_lines, _ = get_test_lines_and_update_lines(
            diff_dict[file_id]
        )

        changed_lines_map[file_id] = changed_lines
        new_line_map[file_id] = line_mapping(updates_to_lines, filename)

        tests = testgetter.get_tests_from_testfiles(changed_lines, file_id)

        for test in tests:
            test_set.add(test)
    return test_set, changed_lines_map, new_line_map


def tests_from_changed_srcfiles(diff_dict, files, mappinghelper, testgetter):
    """
    Calculate test set,
    update data
    and warning for untested new lines from changes to a source code file
    """

    test_set = set()
    changed_lines_map = {}
    new_line_map = {}
    files_to_warn = []
    for srcfile in files:
        file_id = srcfile[0]
        filename = srcfile[1]
        changed_lines, updates_to_lines, new_lines = get_test_lines_and_update_lines(
            diff_dict[file_id]
        )

        changed_lines_map[file_id] = changed_lines
        new_line_map[file_id] = line_mapping(updates_to_lines, filename)

        if any(
            [
                not mappinghelper.line_exists(file_id, line_number)
                for line_number in new_lines
            ]
        ):
            files_to_warn.append(filename)

        test_set.update(testgetter.get_tests_from_srcfiles(changed_lines, file_id))

    return test_set, changed_lines_map, new_line_map, files_to_warn


def split_changes(changed_files, mappinghelper):
    """Split given changed files into changed testfiles and source code files"""
    changed_testfiles = []
    changed_srcfiles = []

    db_testfiles = mappinghelper.testfiles
    db_srcfiles = mappinghelper.srcfiles

    for changed_file in changed_files:
        for srcfile in db_srcfiles:
            path_to_file = srcfile[1]
            if changed_file == path_to_file:
                changed_srcfiles.append(srcfile)
        for testfile in db_testfiles:
            path_to_file = testfile[1]
            if changed_file == path_to_file:
                changed_testfiles.append(testfile)

    return changed_testfiles, changed_srcfiles


def run_new_test_collection():
    """Run collect plugin"""
    subprocess.run(["pytest_rts_collect"], check=True)


def line_mapping(updates_to_lines, filename, project_folder="."):
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


def calculate_func_lines(src_code):
    """Calculate start and end line numbers for all functions in given code string"""
    parsed_src_code = ast.parse(src_code)
    func_lines = function_lines(parsed_src_code, len(src_code.splitlines()))
    func_mapping = {}
    for line in func_lines:
        func = line[0]
        start = line[1]
        end = line[2]
        func_mapping[func] = (start, end)
    return func_mapping
