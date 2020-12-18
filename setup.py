"""
Setup harness
"""
import subprocess

from setuptools import setup, find_packages  # type: ignore


def _read_long_description():
    with open("README.md") as readme:
        return readme.read()


GIT_VERSION = subprocess.check_output("git describe --always".split()).strip().decode("ascii")
DEV_REQUIRE = [
    "pytest-cov", "pytest-socket", "tox", "python-semantic-release", "black", "mypy",
    "pylint", "safety"
]

# pylint: disable=line-too-long
setup(
    name="pytest_rts",
    description="Coverage-based regression test selection (RTS) plugin for pytest",
    long_description=_read_long_description(),
    author="Eero Kauhanen, Matvey Pashkovskiy, Alexey Vyskubov",
    version=GIT_VERSION,
    packages=find_packages(exclude=("tests.*",)),
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
    extras_require={"dev": DEV_REQUIRE},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
