"""
Setup harness
"""
import subprocess

from setuptools import setup, find_packages  # type: ignore


GIT_VERSION = subprocess.check_output("git describe --always".split()).strip().decode("ascii")
DEV_REQUIRE = ["pytest-cov", "pytest-socket", "tox", "python-semantic-release", "black", "mypy", "pylint", "safety"]

# pylint: disable=line-too-long
setup(
    name="pytest_rts",
    version=GIT_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pytest_rts_eval=pytest_rts.tests.evaluation.start:main",
            "pytest_rts_specific_without_remap=pytest_rts.tests.evaluation.specific_without_remap:main",
            "pytest_rts_all_without_remap=pytest_rts.tests.evaluation.all_without_remap:main",
            "pytest_rts_collect=pytest_rts.collect:main",
        ],
        "pytest11": [
            "pytest-rts=pytest_rts.plugin",
        ],
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={
        "dev": TESTS_REQUIRE + DEV_REQUIRE,
    },
)
