import pytest


def test_full_integration(helper):
    helper.checkout_new_branch()

    # Add a new method to source file
    helper.change_file("changes/car/add_new_method.txt", "src/car.py")

    # Get changed src file id
    src_file_id = helper.get_mapping_id_from_filename("src/car.py", is_srcfile=True)

    # Get working directory test_set like in pytest_rts script
    workdir_test_set = helper.get_tests_from_tool_current()

    # New method addition = no new tests should be found
    assert not workdir_test_set

    # Run pytest_rts, db shouldn't update
    old_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    helper.run_tool()
    new_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)

    assert old_srcfile_lines == new_srcfile_lines

    # Commit changes
    helper.commit_change("src/car.py", "new_method_src")

    # Get committed changes test_set like in pytest_rts script
    commit_test_set = helper.get_tests_from_tool_committed()

    # New method addition = no new tests should be found
    assert not commit_test_set

    # DB should update after running test selector
    # But no new test tests new method so lines should be the same
    helper.run_tool()
    new_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_srcfile_lines == new_srcfile_lines

    # Add a new test method
    helper.change_file("changes/test_car/add_test_passengers.txt", "tests/test_car.py")

    # Get working directory diffs and test_set like in pytest_rts script
    workdir_test_set2 = helper.get_tests_from_tool_current()

    # Changes test_set should be empty
    assert not workdir_test_set2

    # Running pytest_rts should not add new test to database
    helper.run_tool()
    assert not helper.new_test_exists_in_mapping_db(
        "tests/test_car.py::test_passengers"
    )

    # Commit changes
    helper.commit_change("tests/test_car.py", "new_test_method")

    # Get committed changes test_set like in pytest_rts script
    commit_test_set2 = helper.get_tests_from_tool_committed()

    # Test_set should now include all tests from changes between this commit and previous
    # = New test method
    assert commit_test_set2 == {"tests/test_car.py::test_passengers"}

    # New tests should include the newly added test only
    new_tests = helper.get_newly_added_tests_from_tool()
    assert new_tests == {"tests/test_car.py::test_passengers"}

    # Running pytest_rts should now update database = new test function should be found in db
    helper.run_tool()
    assert helper.new_test_exists_in_mapping_db("tests/test_car.py::test_passengers")


def test_db_updating_only_once(helper):
    helper.checkout_new_branch()

    filename = "src/car.py"
    change = "changes/car/shift_2_forward.txt"
    expected_lines = [6, 7, 8, 11, 14]

    src_file_id = helper.get_mapping_id_from_filename(filename, is_srcfile=True)
    old_lines = helper.get_mapping_lines_for_srcfile(src_file_id)

    # Change src file
    helper.change_file(change, filename)

    # Changes in working directory, run pytest_rts
    # Shouldn't update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines == new_lines

    # Commit changes
    helper.commit_change(filename, "commit1")

    # Committed changes, run pytest_rts
    # Should update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines != new_lines
    assert new_lines == expected_lines

    # Run again, shouldn't update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert new_lines == expected_lines


def test_skipping_commit(helper):
    # Checkout a new branch
    helper.checkout_new_branch()

    # Change file from changes folder and commit changes
    first_change, first_filename = (
        "changes/car/change_accelerate.txt",
        "src/car.py",
    )
    helper.change_file(first_change, first_filename)
    helper.commit_change(first_filename, "commit1")

    # Run tests selector and db should update
    helper.run_tool()

    # Change shop.py from changes folder and commit changes
    second_change, second_filename = (
        "changes/shop/change_get_price.txt",
        "src/shop.py",
    )
    helper.change_file(second_change, second_filename)
    helper.commit_change(second_filename, "commit2")

    # Change test_car.py from changes folder and commit changes
    third_change, third_filename = (
        "changes/test_car/add_test_passengers.txt",
        "tests/test_car.py",
    )
    helper.change_file(third_change, third_filename)
    helper.commit_change(third_filename, "commit3")

    # Tests selectors functions should find tests from changes:
    # Commit1 -> Commit2 AND Commit2 -> Commit3
    # DB required to use the function
    test_set = helper.get_tests_from_tool_committed()
    assert test_set == {
        "tests/test_shop.py::test_normal_shop_purchase2",
        "tests/test_shop.py::test_normal_shop_purchase",
        "tests/test_car.py::test_passengers",
    }


def test_squashing_commits(helper):
    helper.checkout_new_branch()

    helper.change_file("changes/car/change_accelerate.txt", "src/car.py")
    helper.commit_change("src/car.py", "commit0")

    helper.change_file("changes/car/add_new_method.txt", "src/car.py")
    helper.commit_change("src/car.py", "commit1")

    # Run tool -> db updated to commit1 state
    helper.run_tool()

    helper.change_file("changes/shop/change_get_price.txt", "src/shop.py")
    helper.commit_change("src/shop.py", "commit2")

    helper.squash_commits(3, "commit3")

    # Tool should find only tests for change introduced in commit1 -> commit2
    assert helper.get_tests_from_tool_committed() == {
        "tests/test_shop.py::test_normal_shop_purchase",
        "tests/test_shop.py::test_normal_shop_purchase2",
    }


def test_init_code_tracked(helper):
    helper.change_file("changes/init/change_function_one.txt", "src/__init__.py")
    assert helper.get_tests_from_tool_current() == {"tests/test_init.py::test_one"}


def test_decorated_tracked(helper):
    """Test that changes in the decorator switch on the test using decorated
    function.
    """
    helper.change_file("changes/decorated/change_decorator.txt", "src/decorators.py")
    assert helper.get_tests_from_tool_current() == {
        "tests/test_decorated.py::test_decorated"
    }


def test_decorated_with_param_tracked(helper):
    """Test that changes in the parametrized decorator switch on the test using
    decorated function.
    """
    helper.change_file("changes/decorated/change_decorator_2.txt", "src/decorators.py")
    assert helper.get_tests_from_tool_current() == {
        "tests/test_decorated.py::test_decorated_2"
    }
