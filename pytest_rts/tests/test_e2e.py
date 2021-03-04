"""E2E tests of the tool"""

from pytest_rts.tests.utils.helper_functions import (
    change_file,
    checkout_new_branch,
    commit_change,
    get_mapping_id_for_srcfile,
    get_mapping_lines_for_srcfile,
    get_newly_added_tests_from_tool,
    get_test_function_runtimes,
    get_tests_from_tool_committed,
    get_tests_from_tool_current,
    new_test_exists_in_mapping_db,
    run_tool,
    squash_commits,
)


def test_full_integration():
    """Test case for running a typical workflow"""
    checkout_new_branch()

    # Add a new method to source file
    change_file("changes/car/add_new_method.txt", "src/car.py")

    # Get changed src file id
    src_file_id = get_mapping_id_for_srcfile("src/car.py")

    # Get working directory test_set like in pytest_rts script
    workdir_test_set = get_tests_from_tool_current()

    # New method addition = no new tests should be found
    assert not workdir_test_set

    # Run pytest_rts, db shouldn't update
    old_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)
    run_tool()
    new_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)

    assert old_srcfile_lines == new_srcfile_lines

    # Commit changes
    commit_change("src/car.py", "new_method_src")

    # Get committed changes test_set like in pytest_rts script
    commit_test_set = get_tests_from_tool_committed()

    # New method addition = no new tests should be found
    assert not commit_test_set

    # DB should update after running test selector
    # But no new test tests new method so lines should be the same
    run_tool()
    new_srcfile_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_srcfile_lines == new_srcfile_lines

    # Add a new test method
    change_file("changes/test_car/add_test_passengers.txt", "tests/test_car.py")

    # Get working directory diffs and test_set like in pytest_rts script
    workdir_test_set2 = get_tests_from_tool_current()

    # Changes test_set should be empty
    assert not workdir_test_set2

    # Running pytest_rts should not add new test to database
    run_tool()
    assert not new_test_exists_in_mapping_db("tests/test_car.py::test_passengers")

    # Commit changes
    commit_change("tests/test_car.py", "new_test_method")

    # Get committed changes test_set like in pytest_rts script
    commit_test_set2 = get_tests_from_tool_committed()

    # Test_set should now include all tests from changes between this commit and previous
    # = New test method
    assert commit_test_set2 == {"tests/test_car.py::test_passengers"}

    # New tests should include the newly added test only
    new_tests = get_newly_added_tests_from_tool()
    assert new_tests == {"tests/test_car.py::test_passengers"}

    # Running pytest_rts should now update database = new test function should be found in db
    run_tool()
    assert new_test_exists_in_mapping_db("tests/test_car.py::test_passengers")


def test_db_updating_only_once():
    """Test case for making sure the database does not update twice"""
    checkout_new_branch()

    filename = "src/car.py"
    change = "changes/car/shift_2_forward.txt"
    expected_lines = [6, 7, 8, 11, 14]

    src_file_id = get_mapping_id_for_srcfile(filename)
    old_lines = get_mapping_lines_for_srcfile(src_file_id)

    # Change src file
    change_file(change, filename)

    # Changes in working directory, run pytest_rts
    # Shouldn't update db
    run_tool()
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines == new_lines

    # Commit changes
    commit_change(filename, "commit1")

    # Committed changes, run pytest_rts
    # Should update db
    run_tool()
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines != new_lines
    assert new_lines == expected_lines

    # Run again, shouldn't update db
    run_tool()
    new_lines = get_mapping_lines_for_srcfile(src_file_id)
    assert new_lines == expected_lines


def test_skipping_commit():
    """Test case for skipping pytest-rts run between commits"""
    # Checkout a new branch
    checkout_new_branch()

    # Change file from changes folder and commit changes
    first_change, first_filename = (
        "changes/car/change_accelerate.txt",
        "src/car.py",
    )
    change_file(first_change, first_filename)
    commit_change(first_filename, "commit1")

    # Run tests selector and db should update
    run_tool()

    # Change shop.py from changes folder and commit changes
    second_change, second_filename = (
        "changes/shop/change_get_price.txt",
        "src/shop.py",
    )
    change_file(second_change, second_filename)
    commit_change(second_filename, "commit2")

    # Change test_car.py from changes folder and commit changes
    third_change, third_filename = (
        "changes/test_car/add_test_passengers.txt",
        "tests/test_car.py",
    )
    change_file(third_change, third_filename)
    commit_change(third_filename, "commit3")

    # Tests selectors functions should find tests from changes:
    # Commit1 -> Commit2 AND Commit2 -> Commit3
    # DB required to use the function
    test_set = get_tests_from_tool_committed()
    assert test_set == {
        "tests/test_shop.py::test_normal_shop_purchase2",
        "tests/test_shop.py::test_normal_shop_purchase",
        "tests/test_car.py::test_passengers",
    }


def test_squashing_commits():
    """Test case for squashing commits"""
    checkout_new_branch()

    change_file("changes/car/change_accelerate.txt", "src/car.py")
    commit_change("src/car.py", "commit0")

    change_file("changes/car/add_new_method.txt", "src/car.py")
    commit_change("src/car.py", "commit1")

    # Run tool -> db updated to commit1 state
    run_tool()

    change_file("changes/shop/change_get_price.txt", "src/shop.py")
    commit_change("src/shop.py", "commit2")

    squash_commits(3, "commit3")

    # Tool should find only tests for change introduced in commit1 -> commit2
    assert get_tests_from_tool_committed() == {
        "tests/test_shop.py::test_normal_shop_purchase",
        "tests/test_shop.py::test_normal_shop_purchase2",
    }


def test_init_code_tracked():
    """Test case for code in __init__.py file"""
    change_file("changes/init/change_function_one.txt", "src/__init__.py")
    assert get_tests_from_tool_current() == {"tests/test_init.py::test_one"}


def test_decorated_tracked():
    """Test that changes in the decorator switch on the test using decorated
    function.
    """
    change_file("changes/decorated/change_decorator.txt", "src/decorators.py")
    assert get_tests_from_tool_current() == {"tests/test_decorated.py::test_decorated"}


def test_decorated_with_param_tracked():
    """Test that changes in the parametrized decorator switch on the test using
    decorated function.
    """
    change_file("changes/decorated/change_decorator_2.txt", "src/decorators.py")
    assert get_tests_from_tool_current() == {
        "tests/test_decorated.py::test_decorated_2"
    }


def test_testfunction_runtimes_not_wiped():
    """Test that checks that test function runtimes are not removed
    from database when running the tool for committed changes
    and a testfile is changed
    """
    orig_runtimes = get_test_function_runtimes()
    checkout_new_branch()

    change_file("changes/test_shop/shift_two_forward.txt", "tests/test_shop.py")
    commit_change("tests/test_shop.py", "shift")

    run_tool()
    new_runtimes = get_test_function_runtimes()

    assert orig_runtimes == new_runtimes
