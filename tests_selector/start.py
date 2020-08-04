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
)

PIPE = subprocess.PIPE

PROJECT_FOLDER = sys.argv[1]


def git_diff_data(filename, commithash1, commithash2):
    git_dir = "./" + PROJECT_FOLDER + "/.git"
    git_data = str(
        subprocess.run(
            [
                "git",
                "--git-dir",
                git_dir,
                "diff",
                "-U0",
                commithash1,
                commithash2,
                "--",
                filename,
            ],
            stdout=PIPE,
            stderr=PIPE,
        ).stdout
    )
    return git_data


def tests_from_changed_testfiles(files, commithash1, commithash2):
    test_set = set()
    changed_lines_dict = {}
    new_line_map_dict = {}
    for f in files:
        file_id = f[0]
        filename = f[1]
        git_data = git_diff_data(filename, commithash1, commithash2)
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
        git_data = git_diff_data(filename, commithash1, commithash2)
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


def read_newly_added_tests():
    conn = sqlite3.connect("example.db")
    c = conn.cursor()
    new_tests = set()
    for t in [x[0] for x in c.execute("SELECT context FROM new_tests").fetchall()]:
        new_tests.add(t)
    conn.close()

    return new_tests


def get_testfiles_and_srcfiles():
    conn = sqlite3.connect("example.db")
    c = conn.cursor()
    test_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM test_file").fetchall()
    ]
    src_files = [
        (x[0], x[1]) for x in c.execute("SELECT id,path FROM src_file").fetchall()
    ]
    conn.close()
    return test_files, src_files


def split_changes(commit1, commit2):
    changed_tests = []
    changed_sources = []
    db_test_files, db_src_files = get_testfiles_and_srcfiles()

    for changed_file in file_changes_between_commits(commit1, commit2):
        for sf in db_src_files:
            path_to_file = sf[1]
            if changed_file == path_to_file:
                changed_sources.append(sf)
        for tf in db_test_files:
            path_to_file = tf[1]
            if changed_file == path_to_file:
                changed_tests.append(tf)

    return changed_tests, changed_sources


def file_changes_between_commits(commit1, commit2):
    git_dir = "./" + PROJECT_FOLDER + "/.git"
    git_data = subprocess.run(
        ["git", "--git-dir", git_dir, "diff", "--name-only", commit1, commit2],
        stdout=PIPE,
        stderr=PIPE,
    ).stdout
    changed_files = str(git_data, "utf-8").strip().split()
    return changed_files


def run_tests_and_update(test_set, update_tuple):
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


def commits_test():
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


# if __name__ == "__main__":
#    main()
