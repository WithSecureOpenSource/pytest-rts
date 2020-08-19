import os
import subprocess

from tests_selector.utils.db import (
    DB_FILE_NAME,
    update_db_from_src_mapping,
    update_db_from_test_mapping,
    delete_ran_lines
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