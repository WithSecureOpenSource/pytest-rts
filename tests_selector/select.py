import subprocess
import sys
import os

from tests_selector.start import get_testfiles_and_srcfiles

from tests_selector.helper import (
    get_test_lines_and_update_lines,
    query_tests_sourcefile,
    delete_ran_lines,
    update_db_from_src_mapping,
    start_normal_phase,
    start_test_init,
)

PIPE = subprocess.PIPE
PROJECT_FOLDER = sys.argv[1]


def line_mapping(updates_to_lines, filename):
    # copy paste from helper because of fixing directory errors for now
    current_dir = os.getcwd()
    project_dir = "./" + PROJECT_FOLDER
    os.chdir(project_dir)
    try:
        line_count = sum(1 for line in open(filename)) - 1
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
    os.chdir(current_dir)
    return line_mapping


def changed_files_current():
    # specifying git dir to this returns strange files so this changes the working directory now
    current_dir = os.getcwd()
    project_dir = "./" + PROJECT_FOLDER
    os.chdir(project_dir)
    git_data = subprocess.run(
        ["git", "diff", "--name-only"], stdout=PIPE, stderr=PIPE,
    ).stdout
    changed_files = str(git_data, "utf-8").strip().split()
    os.chdir(current_dir)
    return changed_files


def changed_source_files():
    db_test_files, db_src_files = get_testfiles_and_srcfiles()
    changed_sources = []
    for changed_file in changed_files_current():
        for sf in db_src_files:
            path_to_file = sf[1]
            if changed_file == path_to_file:
                changed_sources.append(sf)
    return changed_sources


def file_diff_data(filename):
    current_dir = os.getcwd()
    project_dir = "./" + PROJECT_FOLDER
    os.chdir(project_dir)
    git_data = str(
        subprocess.run(
            ["git", "diff", "-U0", filename,], stdout=PIPE, stderr=PIPE,
        ).stdout
    )
    os.chdir(current_dir)
    return git_data


def run_tests_and_update_db(test_set, update_tuple):
    # a bit different than the one in start.py for now
    changed_lines_src = update_tuple[0]
    line_map_src = update_tuple[1]

    for file_id in changed_lines_src.keys():
        delete_ran_lines(changed_lines_src[file_id], file_id)
        update_db_from_src_mapping(line_map_src[file_id], file_id)

    start_normal_phase(PROJECT_FOLDER, test_set)


def run():
    # runs tests based on changes in source files
    # will add tests based on changed test files next commit

    ans = input("init db? [y/n]: ")
    if ans == "y":
        start_test_init(PROJECT_FOLDER)

    changed_files = changed_source_files()
    print(f"found {len(changed_files)} changed src files")
    test_line_dict = {}
    new_line_map_dict = {}

    for changed_file in changed_files:
        filename = changed_file[1]
        file_id = changed_file[0]

        file_diff = file_diff_data(filename)
        lines_to_query, updates_to_lines = get_test_lines_and_update_lines(file_diff)

        test_line_dict[file_id] = lines_to_query  # contains changed lines
        new_line_map_dict[file_id] = line_mapping(
            updates_to_lines, filename
        )  # new line mapping

    # new loop for clarity at this time
    test_set = set()
    update_tuple = (test_line_dict, new_line_map_dict)
    for file_id in test_line_dict.keys():
        tests_from_changes = query_tests_sourcefile(test_line_dict[file_id], file_id)
        for t in tests_from_changes:
            test_set.add(t)

    if len(test_set) > 0:
        print(f"found {len(test_set)} tests")
        ans = input("run tests? [y/n]: ")
        if ans == "y":
            run_tests_and_update_db(test_set, update_tuple)
        # now the database is updated with new mapping but git diff still remains the same
        # whats the best way to handle that?
    else:
        print("no tests")


def main():
    run()


if __name__ == "__main__":
    main()
