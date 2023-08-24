from setuptools import setup, find_packages

setup(
    entry_points={"console_scripts": []},
    packages=(find_packages(where=".")),
    package_dir={"": "."},
    test_suite="tests.subworkflow_test_suite",
    install_requires=[
        "requests",
        "cwltool",
        "click",
        "loguru",
    ],
    scripts=["bin/ap-validator"],
    project_urls={
        "Documentation": "https://github.com/EOEPCA/app-package-validation/blob/main/README.md",
        "Source": "https://github.com/EOEPCA/app-package-validation/",
        "Tracker": "https://github.com/EOEPCA/app-package-validation/issues",
    },
)
