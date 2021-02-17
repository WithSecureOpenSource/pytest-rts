"""Helper functions for evaluation code"""
import logging
import random
import subprocess
from typing import List, Set

from pytest_rts.utils.git import (
    get_git_repo,
    get_current_head_hash,
    changed_files_between_commits,
)
from pytest_rts.models.source_file import SourceFile
from pytest_rts.models.test_function import TestFunction
from pytest_rts.models.test_map import TestMap
from pytest_rts.tests.session_wrapper import with_session
from pytest_rts.utils.mappinghelper import MappingHelper


def full_diff_between_commits(commit1, commit2) -> str:
    """Git diff between commits"""
    repo = get_git_repo(None).repo.git
    return repo.diff(commit1, commit2)


def select_random_file(files) -> str:
    """Select a random source file from list"""
    return random.choice(files)


def delete_random_line(filepath):
    """Replace a random line containing code to a newline"""
    try:
        with open(filepath, "r") as randomfile:
            data = randomfile.readlines()
            while True:
                rand_line = random.randint(0, len(data) - 1)
                if data[rand_line] != "\n":
                    break
            data[rand_line] = "\n"  # replace random line with newline.

        with open(filepath, "w") as randomfile:
            for line in data:
                randomfile.write(line)

    except FileNotFoundError:
        logging.getLogger().error(f"can't open selected random file {filepath}")
        exit(1)


def capture_specific_exit_code(tests, max_wait) -> int:
    """Run pytest with a given test set and capture exit code"""
    try:
        specific_exit_code = subprocess.run(
            ["pytest_rts_capture_exitcode"] + tests,
            timeout=max_wait,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=False,
        ).returncode
    except subprocess.TimeoutExpired:
        specific_exit_code = -1

    return specific_exit_code


def capture_all_exit_code(max_wait) -> int:
    """Run entire pytest test suite and capture exit code"""
    try:
        all_exit_code = subprocess.run(
            ["pytest", "-p", "no:terminal"],
            timeout=max_wait,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=False,
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
    logger,
):
    """Print random remove test statistics"""
    logger.info("============")
    logger.info(f"iteration: {i+1}")
    logger.info(f"project name: {project_name}")
    logger.info(f"commit hash: {commithash}")
    logger.info(f"removed {deletes} random src file lines")
    logger.info(f"size of full test suite: {full_test_suite_size}")
    logger.info(f"size of line level test suite: {line_test_suite_size}")
    logger.info(f"size of file level test suite: {file_test_suite_size}")
    logger.info(
        f"exitcodes: line-level: {exitcode_line}, file-level: {exitcode_file}, all: {exitcode_all}"
    )
    logger.info(f"STORING TO DATABASE: {db_name}")
    logger.info("============")


@with_session
def get_test_suite_size(session=None) -> int:
    """Query how many tests are in mapping database"""
    return session.query(TestFunction).count()


@with_session
def get_all_tests_for_srcfile(file_id, session=None) -> List[str]:
    """Query all tests for a source code file"""
    return [
        testfunction.name
        for testfunction in session.query(TestFunction.name)
        .join(TestMap)
        .filter(TestMap.file_id == file_id)
    ]


@with_session
def get_srcfile_id(path, session=None) -> int:
    """Get the id in the mapping database for a source code file"""
    return MappingHelper(session)._get_srcfile(path)


def get_file_level_tests_between_commits(commit1, commit2) -> Set[str]:
    """Get the file-level granularity test set between git commits"""
    return {
        test
        for path in changed_files_between_commits(commit1, commit2)
        for test in get_all_tests_for_srcfile(get_srcfile_id(path))
    }


@with_session
def get_mapping_srcfiles(session=None) -> List[str]:
    """Get all the tool's covered source code files"""
    return [x.path for x in MappingHelper(session).srcfiles]


@with_session
def get_mapping_init_hash(session=None) -> str:
    """Get the git commit hash for initial state of the mapping database"""
    return MappingHelper(session).last_update_hash
