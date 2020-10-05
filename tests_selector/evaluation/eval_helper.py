import os
import subprocess
import random


def select_random_file(files):
    return random.choice(files)


def delete_random_line(filename, project_folder):
    try:
        with open(os.getcwd() + "/" + project_folder + "/" + filename, "r") as f:
            data = f.readlines()
            while True:
                rand_line = random.randint(0, len(data) - 1)
                if data[rand_line] != "\n":
                    break
            data[rand_line] = "\n"  # replace random line with newline.

        with open(os.getcwd() + "/" + project_folder + "/" + filename, "w") as f:
            for line in data:
                f.write(line)

    except FileNotFoundError:
        print("can't open selected random file")
        exit(1)


def capture_specific_exit_code(tests, project_folder, max_wait):
    # 30 second timeout for tests in case of loop
    try:
        specific_exit_code = subprocess.run(
            ["tests_selector_specific_without_remap", project_folder] + tests,
            timeout=max_wait,
            capture_output=True,
        ).returncode
    except subprocess.TimeoutExpired:
        specific_exit_code = -1

    return specific_exit_code


def capture_all_exit_code(project_folder, max_wait):
    try:
        all_exit_code = subprocess.run(
            ["tests_selector_all_without_remap", project_folder],
            timeout=max_wait,
            capture_output=True,
        ).returncode
    except subprocess.TimeoutExpired:
        all_exit_code = -1

    return all_exit_code


def print_remove_test_output(
    i,
    project_name,
    commithash,
    deletes,
    full_test_suite_size,
    line_test_suite_size,
    file_test_suite_size,
    exitcode_line,
    exitcode_file,
    exitcode_all,
    db_name,
):
    print("============")
    print("iteration:", i + 1)
    print("project name:", project_name)
    print("commit hash:", commithash)
    print(f"removed {deletes} random src file lines")
    print("size of full test suite:", full_test_suite_size)
    print("size of line level test suite:", line_test_suite_size)
    print("size of file level test suite:", file_test_suite_size)
    print(
        f"exitcodes: line-level: {exitcode_line}, file-level: {exitcode_file}, all: {exitcode_all}"
    )
    print("STORING TO DATABASE:", db_name)
    print("============")


def tests_from_changes_between_commits(commithash1, commithash2, project_folder, db):
    changed_files = file_changes_between_commits(
        commithash1, commithash2, project_folder
    )

    changed_test_files, changed_src_files = split_changes(changed_files, db)

    diff_dict_src = file_diff_dict_between_commits(
        changed_src_files, commithash1, commithash2, project_folder
    )
    diff_dict_test = file_diff_dict_between_commits(
        changed_test_files, commithash1, commithash2, project_folder
    )
    (
        test_test_set,
        test_changed_lines_dict,
        test_new_line_map_dict,
    ) = tests_from_changed_testfiles(diff_dict_test, changed_test_files)
    (
        src_test_set,
        src_changed_lines_dict,
        src_new_line_map_dict,
    ) = tests_from_changed_srcfiles(diff_dict_src, changed_src_files)

    test_set = test_test_set.union(src_test_set)
    update_tuple = (
        test_changed_lines_dict,
        test_new_line_map_dict,
        src_changed_lines_dict,
        src_new_line_map_dict,
    )

    return test_set, update_tuple


def install_dependencies(install_cmd, project_folder):
    old_dir = os.getcwd()
    os.chdir("./" + project_folder)
    subprocess.run(install_cmd.split(), capture_output=True)
    os.chdir(old_dir)