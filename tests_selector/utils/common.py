import ast
import os
import subprocess

from tests_selector.utils.db import (
    DB_FILE_NAME,
    delete_ran_lines,
    get_cursor,
    get_testfiles_and_srcfiles,
    query_tests_sourcefile,
    query_tests_testfile,
    update_db_from_test_mapping,
    update_db_from_src_mapping,
)
from tests_selector.utils.git import (
    file_changes_between_commits,
    file_diff_data_between_commits,
    file_diff_data_current,
    file_diff_data_branch,
    get_test_lines_and_update_lines,
)

COVERAGE_CONF_FILE_NAME = ".coveragerc"


def tests_from_changes_between_commits(commithash1, commithash2, project_folder):
    changed_files = file_changes_between_commits(
        commithash1, commithash2, project_folder
    )
    changed_test_files, changed_source_files = split_changes(changed_files)
    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles_between_commits(
        changed_test_files, commithash1, commithash2, project_folder
    )
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_sourcefiles_between_commits(
        changed_source_files, commithash1, commithash2, project_folder
    )

    test_set = test_test_set.union(src_test_set)
    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )

    return test_set, update_tuple


def tests_from_changed_testfiles_between_commits(
    files, commithash1, commithash2, project_folder
):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_commits(
            filename, commithash1, commithash2, project_folder
        )
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_sourcefiles_between_commits(
    files, commithash1, commithash2, project_folder
):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_commits(
            filename, commithash1, commithash2, project_folder
        )
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def run_tests_and_update_db(test_set, update_tuple, project_folder):
    changed_lines_test = update_tuple[
        0
    ]  # TODO: `changed_lines_test` is not used below!
    line_map_test = update_tuple[1]
    changed_lines_src = update_tuple[2]
    line_map_src = update_tuple[3]

    for t in line_map_test.keys():
        update_db_from_test_mapping(line_map_test[t], t)

    for f in changed_lines_src.keys():
        delete_ran_lines(changed_lines_src[f], f)
        update_db_from_src_mapping(line_map_src[f], f)

    start_normal_phase(project_folder, test_set)


def tests_from_changed_sourcefiles_branch(files, project_folder="."):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_branch(filename, project_folder)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_testfiles_branch(files, project_folder="."):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_branch(filename, project_folder)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_sourcefiles_current(files, project_folder="."):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_current(filename, project_folder)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_testfiles_current(files, project_folder="."):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_current(filename, project_folder)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, project_folder)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def split_changes(changed_files):
    changed_tests = []
    changed_sources = []
    db_test_files, db_src_files = get_testfiles_and_srcfiles()

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


def read_newly_added_tests(project_folder="."):
    subprocess.run(["tests_selector_collect", project_folder])
    c, conn = get_cursor()
    new_tests = set()
    for t in [x[0] for x in c.execute("SELECT context FROM new_tests").fetchall()]:
        new_tests.add(t)
    conn.close()
    return new_tests


def line_mapping(updates_to_lines, filename, PROJECT_FOLDER):
    try:
        line_count = sum(1 for line in open("./" + PROJECT_FOLDER + "/" + filename))
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


def start_test_init(project_folder):
    if os.path.exists(DB_FILE_NAME):
        os.remove(DB_FILE_NAME)

    if os.path.exists("./" + project_folder + "/" + COVERAGE_CONF_FILE_NAME):
        os.remove("./" + project_folder + "/" + COVERAGE_CONF_FILE_NAME)

    os.rename(
        os.getcwd() + "/" + COVERAGE_CONF_FILE_NAME,
        os.getcwd() + "/" + project_folder + "/" + COVERAGE_CONF_FILE_NAME,
    )

    curr_dir = os.getcwd()
    os.chdir(curr_dir + "/" + project_folder)
    subprocess.run(["tests_selector_init"])
    os.chdir(curr_dir)

    os.rename(
        os.getcwd() + "/" + project_folder + "/" + DB_FILE_NAME,
        os.getcwd() + "/" + DB_FILE_NAME,
    )
    os.rename(
        os.getcwd() + "/" + project_folder + "/" + COVERAGE_CONF_FILE_NAME,
        os.getcwd() + "/" + COVERAGE_CONF_FILE_NAME,
    )


def start_normal_phase(project_folder, test_set):
    os.rename(
        os.getcwd() + "/" + DB_FILE_NAME,
        os.getcwd() + "/" + project_folder + "/" + DB_FILE_NAME,
    )
    if os.path.exists("./" + project_folder + "/" + COVERAGE_CONF_FILE_NAME):
        os.remove("./" + project_folder + "/" + COVERAGE_CONF_FILE_NAME)
    os.rename(
        os.getcwd() + "/" + COVERAGE_CONF_FILE_NAME,
        os.getcwd() + "/" + project_folder + "/" + COVERAGE_CONF_FILE_NAME,
    )

    curr_dir = os.getcwd()
    os.chdir(curr_dir + "/" + project_folder)
    subprocess.run(["tests_selector_run"] + list(test_set))
    os.chdir(curr_dir)

    os.rename(
        os.getcwd() + "/" + project_folder + "/" + DB_FILE_NAME, "./" + DB_FILE_NAME
    )
    os.rename(
        os.getcwd() + "/" + project_folder + "/.coveragerc",
        "./" + COVERAGE_CONF_FILE_NAME,
    )


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


def check_create_coverage_conf():
    if os.path.isfile(COVERAGE_CONF_FILE_NAME):
        print(f"file {COVERAGE_CONF_FILE_NAME} already exists")
        return

    with open(COVERAGE_CONF_FILE_NAME, "w") as coverage_config_file:
        coverage_config_file.writelines("[run]\nomit = */.venv/*, tests/*, /tmp/*, *__init__*")
