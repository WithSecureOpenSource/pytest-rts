import pytest


@pytest.mark.parametrize(
    "new_method_srcfile, new_method_testfile",
    [
        (
            ("changes/car/add_new_method.txt", "src/car.py"),
            (
                "changes/test_car/add_test_passengers.txt",
                "tests/test_car.py",
                "tests/test_car.py::test_passengers",
            ),
        ),
    ],
)
def test_full_integration(new_method_srcfile, new_method_testfile, helper):
    helper.checkout_new_branch()

    change_for_new_src_method = new_method_srcfile[0]
    filename_for_new_src_method = new_method_srcfile[1]
    src_file_id = helper.get_mapping_id_from_filename(
        filename_for_new_src_method, is_srcfile=True
    )

    change_for_new_test = new_method_testfile[0]
    filename_for_new_test = new_method_testfile[1]
    new_test_name = new_method_testfile[2]

    # Add a new method to source file
    helper.change_file(change_for_new_src_method, filename_for_new_src_method)

    all_tests_srcfile = helper.get_all_tests_for_srcfile(src_file_id)
    # Get working directory test_set like in tests_selector script
    workdir_test_set = helper.get_tests_from_tool_current()

    # New method addition = test_set should be all tests of that file
    assert workdir_test_set == set(all_tests_srcfile)

    # Run tests_selector, db shouldn't update
    old_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    helper.run_tool()
    new_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)

    assert old_srcfile_lines == new_srcfile_lines

    # Commit changes
    helper.commit_change(filename_for_new_src_method, "new_method_src")

    # Get committed changes test_set like in tests_selector script
    commit_test_set = helper.get_tests_from_tool_committed()

    # New method addition = test_set should be all tests of that file
    assert commit_test_set == set(all_tests_srcfile)

    # DB should update after running test selector
    # But no new test tests new method so lines should be the same
    helper.run_tool()
    new_srcfile_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_srcfile_lines == new_srcfile_lines

    # Add a new test method
    helper.change_file(change_for_new_test, filename_for_new_test)

    # Get working directory diffs and test_set like in tests_selector script
    workdir_test_set2 = helper.get_tests_from_tool_current()
    # Changes test_set should be empty
    # But newline at the end existing test is also considered a change
    assert workdir_test_set2 == set()

    # Running test_selector should not add new test to database
    helper.run_tool()
    assert not helper.new_test_exists_in_mapping_db(new_test_name)

    # Commit changes
    helper.commit_change(filename_for_new_test, "new_test_method")

    # Get committed changes test_set like in tests_selector script
    commit_test_set2 = helper.get_tests_from_tool_committed()

    # Test_set should now include all tests from changes between this commit and previous
    # = New test method + newline causing acceleration test to show up
    assert commit_test_set2 == {new_test_name}

    # New tests should include the newly added test only
    new_tests = helper.get_newly_added_tests_from_tool()
    assert new_tests == {new_test_name}

    # Running tests_selector should now update database = new test function should be found in db
    helper.run_tool()
    assert helper.new_test_exists_in_mapping_db(new_test_name)


@pytest.mark.parametrize(
    "change, new_mapping, filename",
    [("changes/car/shift_2_forward.txt", [6, 7, 8, 11, 14], "src/car.py")],
)
def test_db_updating_only_once(change, new_mapping, filename, helper):
    helper.checkout_new_branch()

    src_file_id = helper.get_mapping_id_from_filename(filename, is_srcfile=True)
    old_lines = helper.get_mapping_lines_for_srcfile(src_file_id)

    # Change src file
    helper.change_file(change, filename)

    # Changes in working directory, run tests_selector
    # Shouldn't update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines == new_lines

    # Commit changes
    helper.commit_change(filename, "commit1")

    # Committed changes, run tests_selector
    # Should update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert old_lines != new_lines
    assert new_lines == new_mapping

    # Run again, shouldn't update db
    helper.run_tool()
    new_lines = helper.get_mapping_lines_for_srcfile(src_file_id)
    assert new_lines == new_mapping


@pytest.mark.parametrize(
    "change_list,expected",
    [
        (
            [
                ("changes/car/change_accelerate.txt", "src/car.py"),
                ("changes/shop/change_get_price.txt", "src/shop.py"),
                ("changes/test_car/add_test_passengers.txt", "tests/test_car.py"),
            ],
            {
                "tests/test_shop.py::test_normal_shop_purchase2",
                "tests/test_shop.py::test_normal_shop_purchase",
                "tests/test_car.py::test_passengers",
            },
        )
    ],
)
def test_skipping_commit(change_list, expected, helper):
    # Checkout a new branch
    helper.checkout_new_branch()

    # Change file from changes folder and commit changes
    first_change, first_filename = change_list[0]
    helper.change_file(first_change, first_filename)
    helper.commit_change(first_filename, "commit1")

    # Run tests selector and db should update
    helper.run_tool()

    # Change shop.py from changes folder and commit changes
    second_change, second_filename = change_list[1]
    helper.change_file(second_change, second_filename)
    helper.commit_change(second_filename, "commit2")

    # Change test_car.py from changes folder and commit changes
    third_change, third_filename = change_list[2]
    helper.change_file(third_change, third_filename)
    helper.commit_change(third_filename, "commit3")

    # Tests selectors functions should find tests from changes:
    # Commit1 -> Commit2 AND Commit2 -> Commit3
    # DB required to use the function
    test_set = helper.get_tests_from_tool_committed()
    assert test_set == expected