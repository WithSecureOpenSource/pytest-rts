from typing import NamedTuple, List, Set, Dict


class UpdateTuple(NamedTuple):
    test_changed_lines_dict: Dict[str, List[int]]
    test_new_line_map_dict: Dict[int, int]
    src_changed_lines_dict: Dict[str, List[int]]
    src_new_line_map_dict: Dict[int, int]


class TestsAndDataFromChanges(NamedTuple):
    test_set: Set[str]
    update_tuple: UpdateTuple
    files_to_warn: List[str]


class TestsAndDataCurrent(NamedTuple):
    test_set: Set[str]
    changed_testfiles_amount: int
    changed_srcfiles_amount: int


class TestsAndDataCommitted(NamedTuple):
    test_set: Set[str]
    update_tuple: UpdateTuple
    changed_testfiles_amount: int
    changed_srcfiles_amount: int
    new_tests_amount: int
    warning_needed: bool
    files_to_warn: List[str]
