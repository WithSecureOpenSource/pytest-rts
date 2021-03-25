"""Integration tests for pytest-rts"""
import os
import subprocess
from typing import Dict, List

import pytest
from _pytest.pytester import Testdir

from pytest_rts.utils.git import get_git_repo

COV_FILE = "rts-coverage.db"


def init_git_repo(tmp_testdir_path: str) -> None:
    """Helper function to initialize a Git repository during tests"""
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], check=True)
    subprocess.run(["git", "config", "user.email", "pytest@example.com"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "1"], check=True)


def commit_change(tmp_testdir_path: str, file_path: str) -> None:
    """Helper function to commit a change to the temporary repo during tests"""
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(
        ["git", "add", file_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "commit", "-m", f"commit {file_path}"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def change_file(
    tmp_testdir_path: str, path_of_change: str, path_to_change: str
) -> None:
    """Helper function to change a file in the testdir during tests"""
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(
        ["cp", "-f", path_of_change, path_to_change],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cleanup_caches(tmp_testdir_path: str) -> None:
    """Helper function to cleanup python and pytest caches
    in testdir between test runs to prevent flakiness
    """
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(
        ["rm", "-rf", "src/__pycache__/"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["rm", "-rf", "tests/__pycache__/"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["rm", "-rf", ".pytest_cache/"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get_testrepo_commithash(tmp_testdir_path: str) -> str:
    """Helper function to return the current Git HEAD in the testrepo"""
    if os.getcwd() != tmp_testdir_path:
        return ""
    repo = get_git_repo()
    return repo.repo.head.object.hexsha


def squash_commits(tmp_testdir_path: str, num_to_squash: int) -> None:
    """Helper function to squash given amount of commits in the testrepo"""
    if os.getcwd() != tmp_testdir_path:
        return
    subprocess.run(["git", "reset", "--soft", f"HEAD~{num_to_squash}"], check=True)
    subprocess.run(["git", "commit", "-m", "squashed_commit"], check=True)


@pytest.fixture(name="testrepo")
def fixture_testrepo(testdir: Testdir) -> Testdir:
    """Run setup for tests in the testdir"""
    testdir.copy_example(".")
    init_git_repo(str(testdir.tmpdir))
    testdir.runpytest_subprocess("--cov=.", "--cov-context=test")
    os.rename(".coverage", COV_FILE)
    cleanup_caches(str(testdir.tmpdir))
    return testdir


def test_only_new_functions_are_ran(testrepo: Testdir) -> None:
    """Test case for running pytest-rts when new tests are added
    and changes are not committed.
    """

    # add a new test method to an existing file
    change_file(
        str(testrepo.tmpdir),
        "changes/test_car/add_test_passengers.txt",
        "tests/test_car.py",
    )

    # add a new test file with a test in it
    testrepo.makepyfile(
        """
        def test_empty():
            assert 1 == 1
    """
    )

    # run pytest-rts to only run new tests
    result = testrepo.runpytest("--rts", f"--rts-coverage-db={COV_FILE}")
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
            {"passed": 0, "failed": 1, "errors": 0},
        ),
        (
            "changes/decorated/change_decorator_2.txt",
            "src/decorators.py",
            {"passed": 0, "failed": 1, "errors": 0},
        ),
        (
            "changes/init/change_function_one.txt",
            "src/__init__.py",
            {"passed": 0, "failed": 1, "errors": 0},
        ),
    ],
)
def test_changes_in_working_directory(
    path_of_change: str,
    path_to_change: str,
    result_dict: Dict[str, int],
    testrepo: Testdir,
) -> None:
    """Test cases for running pytest-rts when changes
    are made in the Git working directory
    """
    # do a change
    change_file(str(testrepo.tmpdir), path_of_change, path_to_change)

    # run pytest-rts to only run tests based on changes
    result = testrepo.runpytest("--rts", f"--rts-coverage-db={COV_FILE}")
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
def test_misused_flags(flags: List[str], returncode: int, testrepo: Testdir) -> None:
    """Test cases for misuse of pytest-rts flags that cause pytest to exit"""
    result = testrepo.runpytest_subprocess(*flags)
    assert result.ret == returncode


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
            {"passed": 0, "failed": 1, "errors": 0},
        ),
        (
            "changes/decorated/change_decorator_2.txt",
            "src/decorators.py",
            {"passed": 0, "failed": 1, "errors": 0},
        ),
        (
            "changes/init/change_function_one.txt",
            "src/__init__.py",
            {"passed": 0, "failed": 1, "errors": 0},
        ),
    ],
)
def test_committed_changes(
    path_of_change: str,
    path_to_change: str,
    result_dict: Dict[str, int],
    testrepo: Testdir,
) -> None:
    """Test cases for running pytest-rts when changes are committed"""
    original_commithash = get_testrepo_commithash(str(testrepo.tmpdir))
    change_file(str(testrepo.tmpdir), path_of_change, path_to_change)
    commit_change(str(testrepo.tmpdir), path_to_change)

    result = testrepo.runpytest(
        "--rts",
        f"--rts-coverage-db={COV_FILE}",
        f"--rts-from-commit={original_commithash}",
    )
    result.assert_outcomes(
        passed=result_dict["passed"],
        failed=result_dict["failed"],
        errors=result_dict["errors"],
    )


def test_commithash_does_not_exist(testrepo: Testdir) -> None:
    """Test case for invalid given commithash where only
    tests from working directory should be collected
    """
    change_file(
        str(testrepo.tmpdir),
        "changes/decorated/change_decorator.txt",
        "src/decorators.py",
    )
    commit_change(str(testrepo.tmpdir), "src/decorators.py")

    change_file(
        str(testrepo.tmpdir),
        "changes/shop/change_get_price.txt",
        "src/shop.py",
    )

    result = testrepo.runpytest(
        "--rts",
        f"--rts-coverage-db={COV_FILE}",
        "--rts-from-commit=does-not-exist",
    )

    result.assert_outcomes(
        passed=2,
        failed=0,
        errors=0,
    )


def test_multiple_commits(testrepo: Testdir) -> None:
    """Test case for running pytest-rts after two commits"""
    original_commithash = get_testrepo_commithash(str(testrepo.tmpdir))
    change_file(
        str(testrepo.tmpdir), "changes/shop/change_get_price.txt", "src/shop.py"
    )
    commit_change(str(testrepo.tmpdir), "src/shop.py")

    change_file(
        str(testrepo.tmpdir),
        "changes/test_car/add_test_passengers.txt",
        "tests/test_car.py",
    )
    commit_change(str(testrepo.tmpdir), "tests/test_car.py")

    result = testrepo.runpytest(
        "--rts",
        f"--rts-coverage-db={COV_FILE}",
        f"--rts-from-commit={original_commithash}",
    )
    result.assert_outcomes(
        passed=3,
        failed=0,
        errors=0,
    )


def test_squashing_commits(testrepo: Testdir) -> None:
    """Test case for running pytest-rts after doing two commits
    and then squashing them into one
    """
    original_commithash = get_testrepo_commithash(str(testrepo.tmpdir))

    change_file(
        str(testrepo.tmpdir), "changes/shop/change_get_price.txt", "src/shop.py"
    )
    commit_change(str(testrepo.tmpdir), "src/shop.py")

    change_file(
        str(testrepo.tmpdir),
        "changes/test_car/add_test_passengers.txt",
        "tests/test_car.py",
    )
    commit_change(str(testrepo.tmpdir), "tests/test_car.py")
    squash_commits(str(testrepo.tmpdir), 2)

    result = testrepo.runpytest(
        "--rts",
        f"--rts-coverage-db={COV_FILE}",
        f"--rts-from-commit={original_commithash}",
    )
    result.assert_outcomes(
        passed=3,
        failed=0,
        errors=0,
    )


def test_both_committed_and_workdir(testrepo: Testdir) -> None:
    """Test case for running tests when there are changes
    both committed and in the working directory
    """
    original_commithash = get_testrepo_commithash(str(testrepo.tmpdir))

    change_file(
        str(testrepo.tmpdir),
        "changes/decorated/change_decorator.txt",
        "src/decorators.py",
    )
    commit_change(str(testrepo.tmpdir), "src/decorators.py")

    change_file(
        str(testrepo.tmpdir),
        "changes/shop/change_get_price.txt",
        "src/shop.py",
    )

    result = testrepo.runpytest(
        "--rts",
        f"--rts-coverage-db={COV_FILE}",
        f"--rts-from-commit={original_commithash}",
    )

    result.assert_outcomes(
        passed=2,
        failed=1,
        errors=0,
    )
