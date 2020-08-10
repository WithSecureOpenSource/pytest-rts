import ast
import os
import sqlite3
import subprocess
import re

from pydriller import GitRepository


def tests_from_changes_between_commits(commithash1, commithash2, PROJECT_FOLDER):
    changed_files = file_changes_between_commits(
        commithash1, commithash2, PROJECT_FOLDER
    )
    changed_test_files, changed_source_files = split_changes(changed_files)
    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles_between_commits(
        changed_test_files, commithash1, commithash2, PROJECT_FOLDER
    )
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_sourcefiles_between_commits(
        changed_source_files, commithash1, commithash2, PROJECT_FOLDER
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
    files, commithash1, commithash2, PROJECT_FOLDER
):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_commits(
            filename, commithash1, commithash2, PROJECT_FOLDER
        )
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename, PROJECT_FOLDER)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_sourcefiles_between_commits(
    files, commithash1, commithash2, PROJECT_FOLDER
):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_commits(
            filename, commithash1, commithash2, PROJECT_FOLDER
        )
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename, PROJECT_FOLDER)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def run_tests_and_update_db(test_set, update_tuple, PROJECT_FOLDER):
    changed_lines_test = update_tuple[0]
    line_map_test = update_tuple[1]
    changed_lines_src = update_tuple[2]
    line_map_src = update_tuple[3]

    for t in line_map_test.keys():
        update_db_from_test_mapping(line_map_test[t], t)

    for f in changed_lines_src.keys():
        delete_ran_lines(changed_lines_src[f], f)
        update_db_from_src_mapping(line_map_src[f], f)

    start_normal_phase(PROJECT_FOLDER, test_set)


def tests_from_changed_sourcefiles_current(files, PROJECT_FOLDER):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_current(filename, PROJECT_FOLDER)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, PROJECT_FOLDER)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_testfiles_current(files, PROJECT_FOLDER):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        file_diff = file_diff_data_current(filename, PROJECT_FOLDER)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(file_diff)
        line_map = line_mapping(updates_to_lines, filename, PROJECT_FOLDER)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def file_changes_between_commits(commit1, commit2, PROJECT_FOLDER):
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git
    return git_helper.diff("--name-only", commit1, commit2).split()


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


def changed_files_current(PROJECT_FOLDER):
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git
    return git_helper.diff("--name-only").split()


def file_diff_data_between_commits(filename, commithash1, commithash2, PROJECT_FOLDER):
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git
    return git_helper.diff("-U0", commithash1, commithash2, "--", filename)


def file_diff_data_current(filename, PROJECT_FOLDER):
    repo = get_git_repo(PROJECT_FOLDER)
    git_helper = repo.repo.git
    return git_helper.diff("-U0", "--", filename)


def get_testfiles_and_srcfiles():
    c, conn = get_cursor()
    test_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM test_file").fetchall()
    ]
    src_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM src_file").fetchall()
    ]
    conn.close()
    return test_files, src_files


def get_cursor():
    conn = sqlite3.connect("mapping.db")
    c = conn.cursor()
    return c, conn


def get_results_cursor():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    return c, conn


def read_newly_added_tests(PROJECT_FOLDER):
    subprocess.run(["tests_collector", PROJECT_FOLDER])
    c, conn = get_cursor()
    new_tests = set()
    for t in [x[0] for x in c.execute("SELECT context FROM new_tests").fetchall()]:
        new_tests.add(t)
    conn.close()

    return new_tests


def get_test_lines_and_update_lines(diff):
    regex = r"[@][@]\s+[-][0-9]+(?:,[0-9]+)?\s+[+][0-9]+(?:,[0-9]+)?\s+[@][@]"
    line_changes = re.findall(regex, diff)
    lines_to_query = []
    updates_to_lines = []
    cum_diff = 0
    for change in line_changes:
        changed_line = change.strip("@").split()
        if "," not in changed_line[0]:
            changed_line[0] += ",1"
        if "," not in changed_line[1]:
            changed_line[1] += ",1"
        old = changed_line[0].split(",")
        old[0] = old[0].strip("-")
        new = changed_line[1].split(",")
        new[0] = new[0].strip("+")

        line_diff = (
            ((int(new[0]) + int(new[1])) - int(new[0]))
            - ((int(old[0]) + int(old[1])) - int(old[0]))
            + cum_diff
        )
        cum_diff = line_diff

        update_tuple = (int(old[0]), line_diff)
        updates_to_lines.append(update_tuple)

        # example data:
        # @@ -old0,old1 +new0,new1 @@
        # old0 to old0 + old1 are now new0 to new0+new1
        # changed lines: old0 to old0 + old1
        # correct?
        if int(old[1]) == 0:
            lines_to_query.append(int(old[0]))
        else:
            for i in range(int(old[0]), int(old[0]) + int(old[1])):
                lines_to_query.append(i)

    return lines_to_query, updates_to_lines


def query_tests_testfile(lines_to_query, file_id):
    cursor, conn = get_cursor()
    tests = []
    for line_id in lines_to_query:
        data = cursor.execute(
            """ SELECT DISTINCT context
                FROM test_function
                WHERE test_file_id = ? 
                AND start <= ?
                AND end >= ?""",
            (file_id, line_id, line_id),
        )
        for line in data:
            test = line[0]
            tests.append(test)
    conn.close()
    return tests


def query_tests_sourcefile(lines_to_query, file_id):
    cursor, conn = get_cursor()
    tests = []
    for line_id in lines_to_query:
        data = cursor.execute(
            """ SELECT DISTINCT context
                FROM test_function
                JOIN test_map ON test_function.id == test_map.test_function_id
                WHERE test_map.file_id = ?
                AND test_map.line_id = ?  """,
            (file_id, line_id,),
        )
        for line in data:
            test = line[0]
            tests.append(test)
    conn.close()
    return tests


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


def delete_ran_lines(line_ids, file_id):
    cursor, conn = get_cursor()
    for line in line_ids:
        cursor.execute(
            "DELETE FROM test_map WHERE line_id == ? AND file_id == ?", (line, file_id)
        )
    conn.close()


def update_db_from_src_mapping(line_map, file_id):
    # this should update test mapping line data of src files to new line numbers calculated from changes
    cursor, conn = get_cursor()
    tests_to_update = []
    for line_id in line_map.keys():
        db_data = cursor.execute(
            "SELECT file_id,test_function_id,line_id FROM test_map WHERE line_id == ? AND file_id == ?",
            (line_id, file_id),
        )
        for line in db_data:
            tests_to_update.append(line)
        cursor.execute(
            "DELETE FROM test_map WHERE line_id == ? AND file_id == ?",
            (line_id, file_id),
        )
    for t in tests_to_update:
        updated_t = (t[0], t[1], line_map[t[2]])
        cursor.execute(
            "INSERT OR IGNORE INTO test_map (file_id,test_function_id,line_id) VALUES (?,?,?)",
            updated_t,
        )
    conn.commit()
    conn.close()


def update_db_from_test_mapping(line_map, file_id):
    # this should update the start and end lines of test functions with new line numbers calculated from changes
    cursor, conn = get_cursor()
    tests_to_update = []
    db_data = cursor.execute(
        """SELECT id,test_file_id,context,start,end FROM test_function
            WHERE test_file_id = ?""",
        (file_id,),
    )
    for line in db_data:
        tests_to_update.append(line)
    cursor.execute("DELETE FROM test_function WHERE test_file_id = ?", (file_id,))

    for t in tests_to_update:
        start = t[3]
        end = t[4]
        if start in line_map:
            start = line_map[start]
        if end in line_map:
            end = line_map[end]
        updated_t = (t[0], t[1], t[2], start, end)
        cursor.execute(
            "INSERT OR IGNORE INTO test_function (id,test_file_id,context,start,end) VALUES (?,?,?,?,?)",
            updated_t,
        )
    conn.commit()
    conn.close()


def start_test_init(PROJECT_FOLDER):
    if os.path.exists("mapping.db"):
        os.remove("mapping.db")

    if os.path.exists("./" + PROJECT_FOLDER + "/.coveragerc"):
        os.remove("./" + PROJECT_FOLDER + "/.coveragerc")

    os.rename(
        os.getcwd() + "/.coveragerc",
        os.getcwd() + "/" + PROJECT_FOLDER + "/.coveragerc",
    )
    subprocess.run(["tests_selector_init", PROJECT_FOLDER])
    os.rename(
        os.getcwd() + "/" + PROJECT_FOLDER + "/mapping.db", os.getcwd() + "/mapping.db"
    )
    os.rename(
        os.getcwd() + "/" + PROJECT_FOLDER + "/.coveragerc",
        os.getcwd() + "/.coveragerc",
    )


def start_normal_phase(PROJECT_FOLDER, test_set):
    os.rename(
        os.getcwd() + "/mapping.db", os.getcwd() + "/" + PROJECT_FOLDER + "/mapping.db"
    )
    if os.path.exists("./" + PROJECT_FOLDER + "/.coveragerc"):
        os.remove("./" + PROJECT_FOLDER + "/.coveragerc")
    os.rename(
        os.getcwd() + "/.coveragerc",
        os.getcwd() + "/" + PROJECT_FOLDER + "/.coveragerc",
    )
    subprocess.run(["tests_selector_run", PROJECT_FOLDER] + list(test_set))
    os.rename(os.getcwd() + "/" + PROJECT_FOLDER + "/mapping.db", "./mapping.db")
    os.rename(os.getcwd() + "/" + PROJECT_FOLDER + "/.coveragerc", "./.coveragerc")


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


def get_git_repo(PROJECT_FOLDER):
    return GitRepository("./" + PROJECT_FOLDER)
