import subprocess
from setuptools import setup


git_version = (
    subprocess.check_output("git describe --always".split()).strip().decode("ascii")
)
tests_require = []
dev_require = ["black"]

setup(
    name="tests_selector",
    version=git_version,
    entry_points={
        "console_scripts": [
            "tests_selector=tests_selector.select:main",
            "tests_selector_eval=tests_selector.start:main",
            "tests_selector_init=tests_selector.init_run:main",
            "tests_selector_run=tests_selector.normal_run:main",
            "tests_selector_specific_without_remap=tests_selector.specific_without_remap:main",
            "tests_selector_all_without_remap=tests_selector.all_without_remap:main",
            "tests_collector=tests_selector.collector:main",
        ]
    },
    install_requires=["pydriller", "coverage", "pytest"],
    extras_require={"tests": tests_require, "dev": tests_require + dev_require},
)
