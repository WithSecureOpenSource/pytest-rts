import subprocess
from setuptools import setup, find_packages


git_version = (
    subprocess.check_output("git describe --always".split()).strip().decode("ascii")
)
tests_require = []
dev_require = ["black"]

setup(
    name="tests_selector",
    version=git_version,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "tests_selector_init=tests_selector.init:main",
            "tests_selector=tests_selector.select:main",
            "tests_selector_eval=tests_selector.evaluation.start:main",
            "tests_selector_run=tests_selector.run:main",
            "tests_selector_specific_without_remap=tests_selector.evaluation.specific_without_remap:main",
            "tests_selector_all_without_remap=tests_selector.evaluation.all_without_remap:main",
            "tests_selector_collect=tests_selector.collect:main",
        ]
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={"tests": tests_require, "dev": tests_require + dev_require},
)
