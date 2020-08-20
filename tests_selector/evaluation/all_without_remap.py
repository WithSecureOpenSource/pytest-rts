import os
import pytest
import sys


def main():
    PROJECT_FOLDER = sys.argv[1]
    os.chdir(os.getcwd() + "/" + PROJECT_FOLDER)
    exit_code = pytest.main(["-p", "no:terminal"])
    exit(int(exit_code))


if __name__ == "__main__":
    main()
