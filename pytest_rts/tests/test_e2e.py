"""Integration tests for pytest-rts"""
import os

from _pytest.pytester import Testdir


def test_only_new_functions_are_ran(testdir: Testdir) -> None:
    """Test case for running pytest-rts when new tests are added
    and changes are not committed.
    """
    # copy the helper project
    testdir.copy_example(".")

    # run pytest pytest-cov to produce mapping
    # subprocess used to not mess up with coverage for this test suite
    testdir.runpytest_subprocess("--cov=.", "--cov-context=test")

    # rename .coverage file produced by pytest-cov
    os.rename(".coverage", "rts-coverage.1234")

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
    result = testdir.runpytest("--rts", "--rts-coverage-db=rts-coverage.1234")
    result.assert_outcomes(passed=2, failed=0, errors=0)
