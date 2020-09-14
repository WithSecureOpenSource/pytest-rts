import pytest
from tests_selector.pytest.fake_item import FakeItem
from tests_selector.utils.db import get_test_duration


class NormalPhasePlugin:
    def __init__(self, test_set):
        self.test_func_times = {}
        self.test_set = test_set
        self.fill_times_dict()

    def fill_times_dict(self):
        for testname in self.test_set:
            self.test_func_times[testname] = get_test_duration(testname)

    def pytest_collection_modifyitems(self, session, config, items):
        original_length = len(items)
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
        # sort tests based on duration value from database
        items[:] = sorted(selected, key=lambda item: self.test_func_times[item.nodeid])

        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )

