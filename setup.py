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
    name="pytest_rts",
    version=GIT_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pytest_rts_eval=pytest_rts.tests.evaluation.start:main",
            "pytest_rts_capture_exitcode=pytest_rts.tests.evaluation.exitcode:main",
            "pytest_rts_collect=pytest_rts.collect:main",
        ],
        "pytest11": [
            "pytest-rts=pytest_rts.plugin",
        ],
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={
        "tests": TESTS_REQUIRE,
        "dev": TESTS_REQUIRE + DEV_REQUIRE,
    },
)
