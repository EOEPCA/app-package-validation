from setuptools import setup, find_packages

setup(
    entry_points={"console_scripts": []},
    packages=(find_packages(where=".")),
    package_dir={"": "."},
    test_suite="tests.subworkflow_test_suite",
)