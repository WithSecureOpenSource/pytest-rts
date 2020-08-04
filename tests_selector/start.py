import os
import sqlite3
import subprocess
import sys
import random

from pydriller import GitRepository
from tests_selector.helper import (
    get_test_lines_and_update_lines,
    query_tests_sourcefile,
    query_tests_testfile,
    line_mapping,
    start_test_init,
    start_normal_phase,
    delete_ran_lines,
    update_db_from_src_mapping,
    update_db_from_test_mapping,
    read_newly_added_tests,
    get_testfiles_and_srcfiles,
    file_diff_data_between_hashes,
    split_changes,
    file_changes_between_commits,
    run_tests_and_update_db,
)

PIPE = subprocess.PIPE

PROJECT_FOLDER = sys.argv[1]


def tests_from_changed_testfiles(files, commithash1, commithash2):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_hashes(filename, commithash1, commithash2)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_testfile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)

    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changed_sourcefiles(files, commithash1, commithash2):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = file_diff_data_between_hashes(filename, commithash1, commithash2)
        changed_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        line_map = line_mapping(updates_to_lines, filename)

        changed_lines_dict[file_id] = changed_lines
        new_line_map_dict[file_id] = line_map
        tests = query_tests_sourcefile(changed_lines, file_id)

        for t in tests:
            test_set.add(t)
    return test_set, changed_lines_dict, new_line_map_dict


def tests_from_changes(commithash1, commithash2):
    changed_test_files, changed_source_files = split_changes(commithash1, commithash2)
    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles(changed_test_files, commithash1, commithash2)
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_sourcefiles(changed_source_files, commithash1, commithash2)

    test_set = test_test_set.union(src_test_set)
    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )

    return test_set, update_tuple


def commits_test():

    # this is now most likely broken
    repo = GitRepository("./" + PROJECT_FOLDER)
    git_commits = list(repo.get_list_commits())

    print(f"repo has {len(git_commits)} commits")
    start = int(input("start commit?"))
    end = int(input("end commit?"))

    error_rates = []

    hash_1 = git_commits[start].hash
    repo.checkout(hash_1)
    start_test_init(PROJECT_FOLDER)

    for commit in git_commits[start + 1 : end]:

        hash_2 = commit.hash
        repo.checkout(hash_2)

        change_test_set, update_tuple = tests_from_changes(hash_1, hash_2)
        subprocess.run(["tests_collector", PROJECT_FOLDER])
        new_tests = read_newly_added_tests()
        final_test_set = change_test_set.union(new_tests)
        run_tests_and_update(final_test_set, update_tuple)

        hash_1 = commit.hash
    repo._delete_tmp_branch()
    # print(error_rates)


def random_remove_test(iterations):

    # this is now most likely broken
    ans = input("init db? [y/n]: ")
    if ans == "y":
        start_test_init(PROJECT_FOLDER)

    test_files, src_files = get_testfiles_and_srcfiles()
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS data (specific_exit INTEGER, all_exit INTEGER)"
    )

    for i in range(iterations):

        while True:
            random_src = random.choice(src_files)
            src_name = random_src[1]
            src_id = random_src[0]
            if PROJECT_FOLDER == src_name[0:4]:
                break

        try:
            with open(os.getcwd() + "/" + PROJECT_FOLDER + "/" + src_name, "r") as f:
                data = f.readlines()
                rand_line = random.randint(0, len(data) - 1)
                data[rand_line] = "\n"
        except FileNotFoundError:
            continue
        with open(os.getcwd() + "/" + PROJECT_FOLDER + "/" + src_name, "w") as f:
            for line in data:
                f.write(line)

        os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
        git_data = str(
            subprocess.run(
                ["git", "diff", "-U0", src_name], stdout=PIPE, stderr=PIPE
            ).stdout
        )
        os.chdir("..")
        test_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
        tests = query_tests_sourcefile(test_lines, src_id)

        try:
            specific_exit_code = int(
                str(
                    subprocess.run(
                        ["tests_selector_specific_without_remap", PROJECT_FOLDER]
                        + tests,
                        capture_output=True,
                        timeout=60,
                    ).stdout,
                    "utf-8",
                ).strip()
            )
        except subprocess.TimeoutExpired:
            specific_exit_code = -1

        try:
            all_exit_code = int(
                str(
                    subprocess.run(
                        ["tests_selector_all_without_remap", PROJECT_FOLDER],
                        capture_output=True,
                        timeout=60,
                    ).stdout,
                    "utf-8",
                ).strip()
            )
        except subprocess.TimeoutExpired:
            all_exit_code = -1

        data_tuple = (specific_exit_code, all_exit_code)
        c.execute("INSERT INTO data VALUES (?,?)", data_tuple)
        conn.commit()

        print("result:", data_tuple, "iteration:", i + 1)
        os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
        subprocess.run(["git", "restore", src_name])
        os.chdir("..")

    conn.close()


def main():
    ans = input("what approach to commits or random_remove? [1/2]: ")
    if ans == "1":
        commits_test()
    elif ans == "2":
        ans = input("how many iterations? ")
        iters = int(ans)
        random_remove_test(iters)


if __name__ == "__main__":
    main()
