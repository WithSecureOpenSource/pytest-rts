import os
import pytest
import sys

def run():

    class NormalPhasePlugin():
        def __init__(self):
            pass

        def pytest_sessionfinish(self, session,exitstatus):
            print(int(exitstatus))

    my_plugin = NormalPhasePlugin()
    pytest.main(['-p','no:terminal'],plugins=[my_plugin])

def main():
    PROJECT_FOLDER = sys.argv[1]
    os.chdir(os.getcwd()+'/'+PROJECT_FOLDER)
    run()

if __name__ == '__main__':
    main()