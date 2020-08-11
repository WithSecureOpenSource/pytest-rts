class CollectPlugin:
    def __init__(self, existing_tests):
        self.collected = []
        self.existing_tests = existing_tests

    def pytest_collection_modifyitems(self, items):
        for item in items:
            if item.nodeid not in self.existing_tests:
                self.collected.append(item.nodeid)
