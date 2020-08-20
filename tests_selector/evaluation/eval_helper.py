import os
import subprocess
import random

from tests_selector.utils.db import (
    DB_FILE_NAME,
    update_db_from_src_mapping,
    update_db_from_test_mapping,
    delete_ran_lines,
)

COVERAGE_CONF_FILE_NAME = ".coveragerc"


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


def select_random_file(files):
    while True:
        random_file = random.choice(files)
        filename = random_file[1]
        if (
            "tests-selector" not in filename
        ):  # for now some tests-selector runners get mapped to source files by accident
            break
    return random_file


def delete_random_line(filename, project_folder):
    try:
        with open(os.getcwd() + "/" + project_folder + "/" + filename, "r") as f:
            data = f.readlines()
            rand_line = random.randint(0, len(data) - 1)
            data[rand_line] = "\n"  # replace random line with newline.

        with open(os.getcwd() + "/" + project_folder + "/" + filename, "w") as f:
            for line in data:
                f.write(line)

    except FileNotFoundError:
        print("can't open selected random file")
        exit(1)


def capture_specific_exit_code(tests, project_folder):
    # 30 second timeout for tests in case of loop
    try:
        specific_exit_code = subprocess.run(
            ["tests_selector_specific_without_remap", project_folder] + tests,
            timeout=30,
            capture_output=True,
        ).returncode
    except subprocess.TimeoutExpired:
        specific_exit_code = -1

    return specific_exit_code


def capture_all_exit_code(project_folder):
    try:
        all_exit_code = subprocess.run(
            ["tests_selector_all_without_remap", project_folder],
            timeout=30,
            capture_output=True,
        ).returncode
    except subprocess.TimeoutExpired:
        all_exit_code = -1

    return all_exit_code
