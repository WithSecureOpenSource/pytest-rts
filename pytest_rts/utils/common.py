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


def tests_from_changed_testfiles(diff_dict, files, db_helper):
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
        tests = db_helper.query_tests_testfile(changed_lines, file_id)

        for test in tests:
            test_set.add(test)
    return test_set, changed_lines_map, new_line_map


def tests_from_changed_srcfiles(diff_dict, files, db_helper):
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
                not db_helper.mapping_line_exists(file_id, line_id)
                for line_id in new_lines
            ]
        ):
            files_to_warn.append(filename)

        tests = db_helper.query_tests_srcfile(changed_lines, file_id)

        for test in tests:
            test_set.add(test)
    return test_set, changed_lines_map, new_line_map, files_to_warn


def split_changes(changed_files, db_helper):
    """Split given changed files into changed testfiles and source code files"""
    changed_tests = []
    changed_sources = []
    db_test_files, db_src_files = db_helper.get_testfiles_and_srcfiles()

    for changed_file in changed_files:
        for srcfile in db_src_files:
            path_to_file = srcfile[1]
            if changed_file == path_to_file:
                changed_sources.append(srcfile)
        for testfile in db_test_files:
            path_to_file = testfile[1]
            if changed_file == path_to_file:
                changed_tests.append(testfile)

    return changed_tests, changed_sources


def read_newly_added_tests(db_helper, project_folder="."):
    """Run collect plugin and read collected new tests from database"""
    subprocess.run(["pytest_rts_collect", project_folder], check=True)
    return db_helper.read_newly_added_tests()


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
        if node.__class__.__name__ == "FunctionDef":
            result.append((node.name, node.body[0].lineno, end))

        for _, field_value in ast.iter_fields(node):
            result.extend(function_lines(field_value, end))

    elif isinstance(node, list):
        for i, item in enumerate(node):
            result.extend(function_lines(item, _next_lineno(i, end)))

    return result


def parse_testfile_from_pytest_item(item):
    """Return testfile path from pytest item"""
    testname = item.nodeid
    testfile = testname.split("::")[0]
    return testfile


def parse_testfunc_from_pytest_item(item):
    """Return test function name from pytest item"""
    func_name = item.name
    func_name_no_params = func_name.split("[")[0]
    return func_name_no_params


def save_testfile_and_func_data(item, elapsed_time, test_func_lines, db_helper):
    """Save testfile and test function"""
    testname = item.nodeid
    testfile = parse_testfile_from_pytest_item(item)
    func_name = parse_testfunc_from_pytest_item(item)
    testfile_id, test_function_id = db_helper.save_testfile_and_func(
        testfile, testname, test_func_lines[testfile][func_name], elapsed_time
    )
    return testfile_id, test_function_id


def save_mapping_data(test_function_id, cov_data, testfiles, db_helper):
    """Save mapping database srcfile and lines covered"""
    for filename in cov_data.measured_files():
        src_file = os.path.relpath(filename, os.getcwd())
        conditions = [
            "pytest-rts" in filename,
            ("/tmp/" in filename) and ("/tmp/" not in os.getcwd()),
            "/.venv/" in filename,
            src_file in testfiles,
            src_file.endswith("conftest.py"),
            not src_file.endswith(".py"),
        ]
        if any(conditions):
            continue
        src_id = db_helper.save_src_file(src_file)
        db_helper.save_mapping_lines(src_id, test_function_id, cov_data.lines(filename))


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


def update_mapping_db(update_data, db_helper):
    """Remove old data from database and shift existing lines if needed"""
    line_map_test = update_data.new_line_map_test
    changed_lines_src = update_data.changed_lines_src
    line_map_src = update_data.new_line_map_src

    for testfile_id in line_map_test.keys():
        # shift test functions
        db_helper.update_db_from_test_mapping(line_map_test[testfile_id], testfile_id)

    for srcfile_id in changed_lines_src.keys():
        # delete ran lines of src file mapping to be remapped by coverage collection
        # shift affected lines by correct amount
        db_helper.delete_ran_lines(changed_lines_src[srcfile_id], srcfile_id)
        db_helper.update_db_from_src_mapping(line_map_src[srcfile_id], srcfile_id)
