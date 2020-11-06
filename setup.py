"""
Setup harness
"""
import subprocess

from setuptools import setup, find_packages  # type: ignore


GIT_VERSION = (
    subprocess.check_output("git describe --always".split()).strip().decode("ascii")
)
TESTS_REQUIRE = ["pytest-cov", "pytest-socket", "tox"]
DEV_REQUIRE = ["black", "mypy", "pylint", "safety"]

# pylint: disable=line-too-long
setup(
    name="tests_selector",
    version=GIT_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "tests_selector_init=tests_selector.init:main",
            "tests_selector=tests_selector.select:main",
            "tests_selector_eval=tests_selector.tests.evaluation.start:main",
            "tests_selector_run=tests_selector.run:main",
            "tests_selector_run_and_update=tests_selector.run_and_update:main",
            "tests_selector_specific_without_remap=tests_selector.tests.evaluation.specific_without_remap:main",
            "tests_selector_all_without_remap=tests_selector.tests.evaluation.all_without_remap:main",
            "tests_selector_collect=tests_selector.collect:main",
        ]
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={
        "tests": TESTS_REQUIRE,
        "dev": TESTS_REQUIRE + DEV_REQUIRE,
    },
)
