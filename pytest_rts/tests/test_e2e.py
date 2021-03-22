"""Integration tests for pytest-rts"""
import os
import subprocess
from typing import Dict, List

import pytest
from _pytest.pytester import Testdir


COV_FILE = "rts-coverage.1234"


def init_git_repo(tmp_testdir_path: str) -> None:
    """Helper function to initialize a Git repository during tests"""
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], check=True)
    subprocess.run(["git", "config", "user.email", "pytest@example.com"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "1"], check=True)


def test_only_new_functions_are_ran(testdir: Testdir) -> None:
    """Test case for running pytest-rts when new tests are added
    and changes are not committed.
    """
    # copy the helper project
    testdir.copy_example(".")

    # make the testdir folder a Git repository
    init_git_repo(str(testdir.tmpdir))

    # run pytest pytest-cov to produce mapping
    # subprocess used to not mess up with coverage for this test suite
    testdir.runpytest_subprocess("--cov=.", "--cov-context=test")

    # rename .coverage file produced by pytest-cov
    os.rename(".coverage", COV_FILE)

    # add a new test method to an existing file
    os.rename("changes/test_car/add_test_passengers.txt", "tests/test_car.py")

    # add a new test file with a test in it
    testdir.makepyfile(
        """
        def test_empty():
            assert 1 == 1
    """
    )

    # run pytest-rts to only run new tests
    result = testdir.runpytest("--rts", f"--rts-coverage-db={COV_FILE}")
    result.assert_outcomes(passed=2, failed=0, errors=0)


@pytest.mark.parametrize(
    "path_of_change, path_to_change, result_dict",
    [
        (
            "changes/shop/change_get_price.txt",
            "src/shop.py",
            {"passed": 2, "failed": 0, "errors": 0},
        ),
        (
            "changes/decorated/change_decorator.txt",
            "src/decorators.py",
            {"passed": 1, "failed": 0, "errors": 0},
        ),
        (
            "changes/decorated/change_decorator_2.txt",
            "src/decorators.py",
            {"passed": 1, "failed": 0, "errors": 0},
        ),
        (
            "changes/init/change_function_one.txt",
            "src/__init__.py",
            {"passed": 1, "failed": 0, "errors": 0},
        ),
    ],
)
def test_changes_in_working_directory(
    path_of_change: str,
    path_to_change: str,
    result_dict: Dict[str, int],
    testdir: Testdir,
) -> None:
    """Test cases for running pytest-rts when changes
    are made in the Git working directory
    """
    # copy the helper project
    testdir.copy_example(".")

    # make the testdir folder a Git repository
    init_git_repo(str(testdir.tmpdir))

    # run pytest pytest-cov to produce mapping
    # subprocess used to not mess up with coverage for this test suite
    testdir.runpytest_subprocess("--cov=.", "--cov-context=test")

    # rename .coverage file produced by pytest-cov
    os.rename(".coverage", COV_FILE)

    # do a change
    os.rename(path_of_change, path_to_change)

    # run pytest-rts to only run tests based on changes
    result = testdir.runpytest("--rts", f"--rts-coverage-db={COV_FILE}")
    result.assert_outcomes(
        passed=result_dict["passed"],
        failed=result_dict["failed"],
        errors=result_dict["errors"],
    )


def test_usage_no_git(testdir: Testdir) -> None:
    """Test case for pytest-rts usage in non-git directory"""
    testdir.copy_example(".")
    testdir.runpytest_subprocess("--cov=.", "--cov-context=test")
    os.rename(".coverage", COV_FILE)

    result = testdir.runpytest_subprocess("--rts", f"--rts-coverage-db={COV_FILE}")
    assert result.ret == 2


@pytest.mark.parametrize(
    "flags, returncode",
    [
        (["--rts"], 2),
        (["--rts", "--rts-coverage-db=does-not-exist"], 2),
    ],
)
def test_misused_flags(flags: List[str], returncode: int, testdir: Testdir) -> None:
    """Test cases for misuse of pytest-rts flags that cause pytest to exit"""
    testdir.copy_example(".")
    init_git_repo(str(testdir.tmpdir))
    result = testdir.runpytest_subprocess(*flags)
    assert result.ret == returncode
