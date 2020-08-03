import os
import pytest
import sys


def run(test_set):
    class NormalPhasePlugin:
        def __init__(self):
            pass

        def pytest_collection_modifyitems(self, session, config, items):
            original_length = len(items)
            selected = []
            for item in items:
                if item.nodeid in test_set:
                    selected.append(item)
            items[:] = selected
            session.config.hook.pytest_deselected(
                items=([FakeItem(session.config)] * (original_length - len(selected)))
            )

        def pytest_sessionfinish(self, session, exitstatus):
            print(int(exitstatus))

    class FakeItem(object):
        def __init__(self, config):
            self.config = config

    my_plugin = NormalPhasePlugin()
    pytest.main(["-p", "no:terminal"], plugins=[my_plugin])


def main():
    PROJECT_FOLDER = sys.argv[1]
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    tests = set(sys.argv[2:])
    run(tests)


if __name__ == "__main__":
    main()
