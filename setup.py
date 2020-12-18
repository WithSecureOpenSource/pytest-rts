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
name = "pytest_rts"
setup(
    name=name,
    description="Coverage-based regression test selection (RTS) plugin for pytest",
    long_description=_read_long_description(),
    author="Eero Kauhanen, Matvey Pashkovskiy, Alexey Vyskubov",
    version=GIT_VERSION,
    packages=find_packages(exclude=[f"{name}.tests", f"{name}.tests.*"]),
    entry_points={
        "console_scripts": [
            f"{name}_eval={name}.tests.evaluation.start:main",
            f"{name}_specific_without_remap={name}.tests.evaluation.specific_without_remap:main",
            f"{name}_all_without_remap={name}.tests.evaluation.all_without_remap:main",
            f"{name}_collect={name}.collect:main",
        ],
        "pytest11": [
            f"pytest-rts={name}.plugin",
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
