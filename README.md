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


## Using the library

Install the library with pip (from PyPI):

```pip install ogc_ap_validator```

Write a quick program using the library (make sure you have the [test CWL file](tests/data/req_8_no_clt_basecommand.cwl) at the correct location):
```
from ap_validator.app_package import AppPackage
import json

ap = AppPackage.from_url("tests/data/req_8_no_clt_basecommand.cwl", entry_point="water_bodies")
result = ap.check_all(include=["error", "hint"])

print(f"VALID:   {result['valid']}")
print(f"CONTENT: {json.dumps(result, indent=2)}")
```

The method `AppPackage.check_all()` returns a dictionary with three entries:

* `valid`: a bool telling the overall validation result, i.e. whether the CWL file is compliant with the OGC application package best practices,
* `issues`: a list of issues (each a dictionary with `type`, `message` and `req` entries). Only issues that match the type in the method's `include` argument are listed (the types are: `error`, `hint` and `note`). The `req` value refers to an OGC requirement (if there is no explicit requirement, the value is `None`), see next point,
* `requirements`: a dictionary where the values are the specifications of all relevant OGC requirements.

Run the program like this:
```
python3 quick-test.py
```

The output will look like this:
```
VALID:   False
CONTENT: {
  "valid": false,
  "issues": [
    {
      "type": "error",
      "message": "Missing element for CommandLineTool 'crop': baseCommand",
      "req": "req-8"
    },
    {
      "type": "hint",
      "message": "No input of type 'Directory' for CommandLineTool 'crop'; make sure inputs referencing GeoJSON features of EO products that need to be staged in are of type 'Directory'",
      "req": "req-12"
    },
    {
      "type": "hint",
      "message": "No input of type 'Directory' for CommandLineTool 'norm_diff'; make sure inputs referencing GeoJSON features of EO products that need to be staged in are of type 'Directory'",
      "req": "req-12"
    },
    {
      "type": "hint",
      "message": "No input of type 'Directory' for CommandLineTool 'otsu'; make sure inputs referencing GeoJSON features of EO products that need to be staged in are of type 'Directory'",
      "req": "req-12"
    },
    {
      "type": "hint",
      "message": "No input of type 'Directory' for CommandLineTool 'stac'; make sure inputs referencing GeoJSON features of EO products that need to be staged in are of type 'Directory'",
      "req": "req-12"
    },
    {
      "type": "hint",
      "message": "No input of type 'Directory' for Workflow 'water_bodies'; make sure inputs referencing GeoJSON features of EO products that need to be staged in are of type 'Directory'",
      "req": "req-13"
    },
    {
      "type": "hint",
      "message": "No output of type 'Directory' for CommandLineTool 'crop'; make sure CommandLineTool outputs that need to be staged are of type 'Directory'",
      "req": "req-14"
    },
    {
      "type": "hint",
      "message": "No output of type 'Directory' for CommandLineTool 'norm_diff'; make sure CommandLineTool outputs that need to be staged are of type 'Directory'",
      "req": "req-14"
    },
    {
      "type": "hint",
      "message": "No output of type 'Directory' for CommandLineTool 'otsu'; make sure CommandLineTool outputs that need to be staged are of type 'Directory'",
      "req": "req-14"
    }
  ],
  "requirements": {
    "req-14": "The outputs field of the CommandLineTool that requires the stage-out of EO products SHALL retrieve all the files produced in the working directory.",
    "req-8": "The Application Package CWL CommandLineTool classes SHALL contain the following elements: Identifier ('id'); Command line name ('baseCommand'); Input parameters ('inputs'); Environment requirements ('requirements'); Docker information ('DockerRequirement').",
    "req-12": "All input parameters of the CWL CommandLineTool that require the staging of EO products SHALL be of type 'Directory'.",
    "req-13": "Input parameters of the CWL Workflow that require the staging of EO products SHALL be of type 'Directory'."
  }
}
```
