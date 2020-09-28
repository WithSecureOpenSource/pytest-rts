import ast
import os
import subprocess
from tests_selector.utils.git import (
    file_diff_data_between_commits,
    file_diff_data_current,
    file_diff_data_branch,
    get_test_lines_and_update_lines,
)


def file_diff_dict_branch(files):
    diff_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        diff = file_diff_data_branch(filename)
        diff_dict[file_id] = diff
    return diff_dict


def file_diff_dict_current(files):
    diff_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        diff = file_diff_data_current(filename)
        diff_dict[file_id] = diff
    return diff_dict


def file_diff_dict_between_commits(files, commithash1, commithash2, project_folder):
    diff_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        diff = file_diff_data_between_commits(
            filename, commithash1, commithash2, project_folder
        )
        diff_dict[file_id] = diff
    return diff_dict


def tests_from_changed_testfiles(diff_dict, files, db):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = diff_dict[file_id]
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = db.query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_srcfiles(diff_dict, files, db):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = diff_dict[file_id]
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = db.query_tests_srcfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def run_tests_and_update_db(test_set, update_tuple, db, project_folder="."):
    changed_lines_test = update_tuple[
        0
    ]  # TODO: `changed_lines_test` is not used below!
    # thinking: no reason to delete the lines / use this

    line_map_test = update_tuple[1]
    changed_lines_src = update_tuple[2]
    line_map_src = update_tuple[3]

    for t in line_map_test.keys():
        # shift test functions
        db.update_db_from_test_mapping(line_map_test[t], t)

    for f in changed_lines_src.keys():
        # delete ran lines of src file mapping to be remapped by coverage collection
        # shift affected lines by correct amount
        db.delete_ran_lines(changed_lines_src[f], f)
        db.update_db_from_src_mapping(line_map_src[f], f)

    if len(test_set) > 0:
        print("Running selected tests...")
        subprocess.run(["tests_selector_run_and_update"] + list(test_set))
    else:
        print("No tests to run")


def split_changes(changed_files, db):
    changed_tests = []
    changed_sources = []
    db_test_files, db_src_files = db.get_testfiles_and_srcfiles()

    for changed_file in changed_files:
        for sf in db_src_files:
            path_to_file = sf[1]
            if changed_file == path_to_file:
                changed_sources.append(sf)
        for tf in db_test_files:
            path_to_file = tf[1]
            if changed_file == path_to_file:
                changed_tests.append(tf)

    return changed_tests, changed_sources


def read_newly_added_tests(db, project_folder="."):
    subprocess.run(["tests_selector_collect", project_folder])
    return db.read_newly_added_tests()


def line_mapping(updates_to_lines, filename, project_folder="."):
    try:
        line_count = sum(1 for line in open("./" + project_folder + "/" + filename))
    except OSError:
        return {}
    line_mapping = {}
    for i in range(len(updates_to_lines)):
        if i + 1 >= len(updates_to_lines):
            next_point = line_count
        else:
            next_point = updates_to_lines[i + 1][0]

        current = updates_to_lines[i][0]
        diff = updates_to_lines[i][1]

        if diff == 0:
            continue
        for k in range(current + 1, next_point + 1):
            line_mapping[k] = k + diff

    return line_mapping


def function_lines(node, end):
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

        for field_name, field_value in ast.iter_fields(node):
            result.extend(function_lines(field_value, end))

    elif isinstance(node, list):
        for i, item in enumerate(node):
            result.extend(function_lines(item, _next_lineno(i, end)))

    return result


def save_data(item, elapsed, test_func_lines, cov_data, testfiles, db):
    testname = item.nodeid
    func_name = item.name
    testfile = testname.split("::")[0]
    func_name_no_params = func_name.split("[")[0]
    line_tuple = test_func_lines[testfile][func_name_no_params]
    func_start = line_tuple[0]
    func_end = line_tuple[1]
    test_file_id, test_function_id = db.save_testfile_and_func(
        testfile, testname, func_name, func_start, func_end, elapsed
    )
    for filename in cov_data.measured_files():
        src_file = os.path.relpath(filename, os.getcwd())
        conditions = [
            "tests-selector" in filename,
            ("/tmp/" in filename) and ("/tmp/" not in os.getcwd()),
            "/.venv/" in filename,
            src_file in testfiles,
            src_file.endswith("__init__.py"),
            src_file.endswith("conftest.py"),
            not src_file.endswith(".py"),
        ]
        if any(conditions):
            continue
        src_id = db.save_src_file(src_file)
        db.save_mapping_lines(src_id, test_function_id, cov_data.lines(filename))


def calculate_func_lines(src_code):
    parsed_src_code = ast.parse(src_code)
    func_lines = function_lines(parsed_src_code, len(src_code.splitlines()))
    lower_dict = {}
    for t in func_lines:
        func = t[0]
        start = t[1]
        end = t[2]
        lower_dict[func] = (start, end)
    return lower_dict
