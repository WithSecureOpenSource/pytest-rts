"""
Setup harness
"""
import subprocess

from setuptools import setup, find_packages  # type: ignore


GIT_VERSION = (
    subprocess.check_output("git describe --always".split()).strip().decode("ascii")
)
TESTS_REQUIRE = ["pytest-cov", "pytest-socket", "tox"]
DEV_REQUIRE = ["black", "mypy", "pylint", "safety", "pandas"]

# pylint: disable=line-too-long
setup(
    name="pytest_rts",
    version=GIT_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pytest_rts_init=pytest_rts.init:main",
            "pytest_rts=pytest_rts.select:main",
            "pytest_rts_eval=pytest_rts.tests.evaluation.start:main",
            "pytest_rts_run=pytest_rts.run:main",
            "pytest_rts_run_and_update=pytest_rts.run_and_update:main",
            "pytest_rts_specific_without_remap=pytest_rts.tests.evaluation.specific_without_remap:main",
            "pytest_rts_all_without_remap=pytest_rts.tests.evaluation.all_without_remap:main",
            "pytest_rts_collect=pytest_rts.collect:main",
        ]
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={
        "tests": TESTS_REQUIRE,
        "dev": TESTS_REQUIRE + DEV_REQUIRE,
    },
)
