# ogc-ap-validator

This repository contains files for testing, building and publishing the validation tool for checking OGC compliance of CWL files for application packages.

The tool checks an input CWL against the CWL-related defined in the [OGC Best Practice for Earth Observation Application Package](https://docs.ogc.org/bp/20-089r1.html)


## Development and debugging

It is recommended to use Visual Studio Code with the provided devcontainer environment.

Install the package locally with:

```
python setup.py install
```

Run streamlit demo:


```
streamlit run demo/app.py
```


## Container

The Dockerfile targets exposing the Application Package streamlit demo via JupyterHub.


## PyPI package

If necessary, change the version in `setup.cfg` and build the PyPI package with the following command:

```
python -m build
```

Upload the package to a PyPI repository (make sure the `dist` directory contains only files of the latest version).
In this example, [test.pypi.org](test.pypi.org) is used.

```
twine upload --verbose -r testpypi dist/*
```

Install the package on any other machine


## Command line tool

After the installation, use the command line tool `ap-validator`

```
Usage: ap-validator [OPTIONS] CWL_URL

  Checks whether the given CWL file (URL or local file path) is compliant with
  the OGC application package best practices

Options:
  --entry-point TEXT              Name of entry point (Workflow or
                                  CommandLineTool)
  --detail [none|errors|hints|all]
                                  Output detail (none|errors|hints|all;
                                  default: hints
  --format [text|json]            Output format (text|json; default: text)
  --help                          Show this message and exit.
  ```

  The validator shows issues and returns an exit code according to the conformance of the CWL file:

  * 0 if the CWL file is a valid application package,
  * 1 if there are missing elements or other clearly identifyable issues,
  * 2 if there is a more fundamental problem with the CWL file.
