from tests_selector.pytest.fake_item import FakeItem


class CaptureSpecificPlugin:
    def __init__(self, test_set):
        self.test_set = test_set

    def pytest_collection_modifyitems(self, session, config, items):
        original_length = len(items)
        selected = []
        for item in items:
            if item.nodeid in self.test_set:
                selected.append(item)
        items[:] = selected
        session.config.hook.pytest_deselected(
            items=([FakeItem(session.config)] * (original_length - len(selected)))
        )
