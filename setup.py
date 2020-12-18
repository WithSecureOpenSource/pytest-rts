"""
Setup harness
"""
import subprocess

from setuptools import setup, find_packages


def _read_long_description():
    with open("README.md") as readme:
        return readme.read()


GIT_VERSION = (
    subprocess
    .check_output("git describe --always".split())
    .strip()
    .decode("ascii")
    .replace("v", "", 1)
)
DEV_REQUIRE = [
    "pytest-cov", "pytest-socket", "tox", "python-semantic-release", "black", "mypy",
    "pylint", "safety"
]
NAME = "pytest_rts"

setup(
    name=NAME,
    description="Coverage-based regression test selection (RTS) plugin for pytest",
    long_description=_read_long_description(),
    author="Eero Kauhanen, Matvey Pashkovskiy, Alexey Vyskubov",
    url=f"https://github.com/F-Secure/{NAME}",
    version=GIT_VERSION,
    packages=find_packages(exclude=[f"{NAME}.tests", f"{NAME}.tests.*"]),
    entry_points={
        "console_scripts": [
            f"{NAME}_eval={NAME}.tests.evaluation.start:main",
            f"{NAME}_specific_without_remap={NAME}.tests.evaluation.specific_without_remap:main",
            f"{NAME}_all_without_remap={NAME}.tests.evaluation.all_without_remap:main",
            f"{NAME}_collect={NAME}.collect:main",
        ],
        "pytest11": [
            f"pytest-rts={NAME}.plugin",
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
