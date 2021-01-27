"""This module contains code for the test selection functionality of the RTS tool"""
from typing import Dict, List, NamedTuple, Set, Tuple
from pytest_rts.utils.common import (
    file_diff_dict_between_commits,
    file_diff_dict_current,
    run_new_test_collection,
    split_changes,
    tests_from_changed_srcfiles,
    tests_from_changed_testfiles,
)
from pytest_rts.utils.git import (
    changed_files_current,
    changed_files_between_commits,
    get_current_head_hash,
)
from pytest_rts.utils.mappinghelper import MappingHelper
from pytest_rts.utils.testgetter import TestGetter


UpdateData = NamedTuple(
    "UpdateData",
    [
        ("changed_lines_test", Dict[int, List[int]]),
        ("new_line_map_test", Dict[int, Dict[int, int]]),
        ("changed_lines_src", Dict[int, List[int]]),
        ("new_line_map_src", Dict[int, Dict[int, int]]),
    ],
)

TestsAndDataFromChanges = NamedTuple(
    "TestsAndDataFromChanges",
    [
        ("test_set", Set[str]),
        ("update_data", UpdateData),
        ("files_to_warn", List[str]),
    ],
)


TestsAndDataCurrent = NamedTuple(
    "TestsAndDataCurrent",
    [
        ("test_set", Set[str]),
        ("changed_testfiles_amount", int),
        ("changed_srcfiles_amount", int),
    ],
)


TestsAndDataCommitted = NamedTuple(
    "TestsAndDataCommitted",
    [
        ("test_set", Set[str]),
        ("update_data", UpdateData),
        ("changed_testfiles_amount", int),
        ("changed_srcfiles_amount", int),
        ("new_tests_amount", int),
        ("warning_needed", bool),
        ("files_to_warn", List[str]),
    ],
)

TestsFromChangesInput = NamedTuple(
    "TestsFromChangesInput",
    [
        ("test_file_diffs", Dict[int, str]),
        ("src_file_diffs", Dict[int, str]),
        ("testfiles", List[Tuple[int, str]]),
        ("srcfiles", List[Tuple[int, str]]),
        ("mappinghelper", MappingHelper),
        ("testgetter", TestGetter),
    ],
)


def get_tests_from_changes(tests_from_changes_input) -> TestsAndDataFromChanges:
    """Returns the test set and data required for line shifting"""
    (
        src_test_set,
        changed_lines_src,
        new_line_map_src,
        files_to_warn,
    ) = tests_from_changed_srcfiles(
        tests_from_changes_input.src_file_diffs,
        tests_from_changes_input.srcfiles,
        tests_from_changes_input.mappinghelper,
        tests_from_changes_input.testgetter,
    )

    (
        test_test_set,
        changed_lines_test,
        new_line_map_test,
    ) = tests_from_changed_testfiles(
        tests_from_changes_input.test_file_diffs,
        tests_from_changes_input.testfiles,
        tests_from_changes_input.testgetter,
    )

    test_set = test_test_set.union(src_test_set)

    update_data = UpdateData(
        changed_lines_test=changed_lines_test,
        new_line_map_test=new_line_map_test,
        changed_lines_src=changed_lines_src,
        new_line_map_src=new_line_map_src,
    )

    return TestsAndDataFromChanges(
        test_set=test_set, update_data=update_data, files_to_warn=files_to_warn
    )


def get_tests_and_data_current(mappinghelper, testgetter) -> TestsAndDataCurrent:
    """Returns the test set from working directory changes and data for printing statistics"""
    changed_files = changed_files_current()
    changed_test_files, changed_src_files = split_changes(changed_files, mappinghelper)

    src_file_diffs = file_diff_dict_current(changed_src_files)
    test_file_diffs = file_diff_dict_current(changed_test_files)

    tests_from_changes_input = TestsFromChangesInput(
        test_file_diffs=test_file_diffs,
        src_file_diffs=src_file_diffs,
        testfiles=changed_test_files,
        srcfiles=changed_src_files,
        mappinghelper=mappinghelper,
        testgetter=testgetter,
    )

    changes = get_tests_from_changes(tests_from_changes_input)

    return TestsAndDataCurrent(
        test_set=changes.test_set,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
    )


def get_tests_and_data_committed(mappinghelper, testgetter) -> TestsAndDataCommitted:
    """Compares current git HEAD has to previous update state commit hash
    Returns the test set and data required for line-shifting and printing statistics
    """
    current_hash = get_current_head_hash()
    previous_hash = mappinghelper.last_update_hash

    changed_files = changed_files_between_commits(previous_hash, current_hash)
    changed_test_files, changed_src_files = split_changes(changed_files, mappinghelper)

    src_file_diffs = file_diff_dict_between_commits(
        changed_src_files, previous_hash, current_hash
    )
    test_file_diffs = file_diff_dict_between_commits(
        changed_test_files, previous_hash, current_hash
    )

    run_new_test_collection()
    new_tests = testgetter.newly_added_tests

    tests_from_changes_input = TestsFromChangesInput(
        test_file_diffs=test_file_diffs,
        src_file_diffs=src_file_diffs,
        testfiles=changed_test_files,
        srcfiles=changed_src_files,
        mappinghelper=mappinghelper,
        testgetter=testgetter,
    )

    changes = get_tests_from_changes(tests_from_changes_input)
    full_test_set = changes.test_set.union(new_tests)

    warning_needed = bool(changes.files_to_warn and not new_tests)

    return TestsAndDataCommitted(
        test_set=full_test_set,
        update_data=changes.update_data,
        changed_testfiles_amount=len(changed_test_files),
        changed_srcfiles_amount=len(changed_src_files),
        new_tests_amount=len(new_tests),
        warning_needed=warning_needed,
        files_to_warn=changes.files_to_warn,
    )
