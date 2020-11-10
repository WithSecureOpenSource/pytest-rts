"""This module contains code to capture pytest exitcode for the entire test suite"""
import pytest


def main():
    exit_code = pytest.main(["-p", "no:terminal"])
    exit(int(exit_code))


if __name__ == "__main__":
    main()
