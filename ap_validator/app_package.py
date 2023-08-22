import sys
import os
import tempfile
from io import StringIO
from typing import Dict
from urllib.parse import urlparse

import requests
import json
import yaml

from cwl_utils.parser import load_document as load_cwl
from cwltool.main import main as cwltool
from requests.exceptions import MissingSchema, InvalidSchema


class AppPackageValidationException(Exception):
    def __init__(self, message, req_text=None):
        self.message = message
        self.req_text = req_text
        super().__init__(self.message)


class AppPackage:

    requirement_specs = {
        "req-7": "The Application Package SHALL be a valid CWL document with a 'Workflow' class "
        "and one or more 'CommandLineTool' classes.",
        "req-8": "The Application Package CWL CommandLineTool classes SHALL contain "
        "the following elements: "
        "Identifier ('id'); Command line name ('baseCommand'); "
        "Input parameters ('inputs'); Environment requirements ('requirements'); "
        "Docker information ('DockerRequirement').",
        "req-9": "The Application Package CWL Workflow class SHALL contain the following elements: "
        "Identifier ('id'); Title ('label'); Abstract ('doc').",
        "req-10": "The Application Package CWL Workflow class “inputs” fields SHALL contain "
        "the following elements: Identifier ('id'); Title ('label'); Abstract ('doc').",
        "req-11": "The Application Package CWL Workclass classes SHALL include additional metadata "
        "as defined in Table 1 (optional: 'author', 'citation', 'codeRepository', 'contributor', "
        "'dateCreated', 'keywords', 'license', 'releaseNotes'; required: 'version').",
        "req-12": "All input parameters of the CWL CommandLineTool that require the staging of "
        "EO products SHALL be of type 'Directory'.",
        "req-13": "Input parameters of the CWL Workflow that require the staging of EO products "
        "SHALL be of type 'Directory'.",
        "req-14": "The outputs field of the CommandLineTool that requires the stage-out of EO products "
        "SHALL retrieve all the files produced in the working directory.",
    }

    def __init__(self, cwl: Dict, entry_point=None) -> None:

        self.cwl = cwl
        self.cwl_obj = load_cwl(cwl, load_all=True)

        self.workflows = [item for item in self.cwl_obj if item.class_ == "Workflow"]
        if entry_point:
            self.workflow = next(
                (wf for wf in self.workflows if wf.id.split("#", 1)[-1] == entry_point), None
            )
        else:
            self.workflow = None
        self.command_line_tools = [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]

    @classmethod
    def process_cli(
        cls,
        cwl_url,
        entry_point=None,
        detail="errors",
        format="text",
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        """Processes a command from the command line interface.

        Parameters
        ----------
        cwl_url : str
            The URL or local file name of the CWL file
        entry_point : str
            The ID of the entry point Workflow or CommandLineTool
        detail : str
            The output detail
        format : str
            The output format
        stdout : object
            Stream for stdout
        stderr : object
            Stream for stderr

        Returns
        -------
        int
            The return code of the command line application
        """

        try:
            ap = cls.from_url(cwl_url, entry_point=entry_point)
        except Exception as e:
            if detail != "none":
                message = "Missing or invalid application package CWL content"
                if format == "text":
                    print(f"ERROR: {message}:\n" f"{str(e)}", file=stdout)
                elif format == "json":
                    print(
                        json.dumps(
                            {
                                "issues": [
                                    {"type": "error", "message": f"{message}: {str(e)}", "req": None}
                                ],
                                "requirements": [],
                            }
                        ),
                        file=stdout,
                    )

            return 2

        include = []
        if detail in ["errors", "hints", "all"]:
            include.append("error")
        if detail in ["hints", "all"]:
            include.append("hint")
        if detail in ["all"]:
            include.append("note")

        result = ap.check_all(include)
        issues = result["issues"]
        valid = result["valid"]

        if format == "text":
            for issue in issues:
                print("{0}: {1}".format(issue["type"].upper(), issue["message"]), file=stdout)
            if valid:
                print(
                    "CWL is compliant with the OGC's Best Practices for Earth Observation "
                    "Application Packages",
                    file=stdout,
                )
            else:
                print(
                    "CWL is NOT compliant with the OGC's Best Practices for Earth Observation "
                    "Application Packages",
                    file=stdout,
                )

        elif format == "json":
            print(json.dumps(result, indent=2), file=stdout)

        return 0 if valid else 1

    @classmethod
    def from_string(cls, cwl_str, entry_point=None):
        """Creates an AppPackage instance from a string.

        Parameters
        ----------
        cwl_str : str
            The string with the CWL (YAML) content
        entry_point : str
            The ID of the entry point Workflow or CommandLineTool

        Returns
        -------
        AppPackage
            An AppPackage instance for the CWL file
        """
        cwl_obj = yaml.safe_load(cwl_str)

        return cls(cwl=cwl_obj, entry_point=entry_point)

    @classmethod
    def from_url(cls, url, entry_point=None):
        """Creates an AppPackage instance from a URL or file name.

        Parameters
        ----------
        url : str
            The URL or local file name of the CWL file
        entry_point : str
            The ID of the entry point Workflow or CommandLineTool

        Returns
        -------
        AppPackage
            An AppPackage instance for the CWL file
        """
        try:
            cwl_content = yaml.safe_load(requests.get(url).text)
        except (MissingSchema, InvalidSchema):
            parsed_url = urlparse(url)
            with open(os.path.abspath(parsed_url.path)) as f:
                cwl_content = yaml.safe_load(f)

        return cls(cwl=cwl_content, entry_point=entry_point)

    def validate_cwl(self):
        """Checks whether the CWL file meets basic conformance criteria.

        Returns
        -------
        tuple
            A tuple containing the return value of cwltool and
            the stdout and stderr content
        """
        temp_dir = tempfile.mkdtemp()
        temp_cwl_path = os.path.join(temp_dir, "temp_cwl")
        with open(temp_cwl_path, "w") as outfile:
            yaml.dump(self.cwl, outfile, default_flow_style=False)

        out = StringIO()
        err = StringIO()
        res = cwltool(
            ["--validate", temp_cwl_path],
            stderr=out,
            stdout=err,
        )
        os.remove(temp_cwl_path)

        return res, out.getvalue(), err.getvalue()

    def check_all(self, include=["error", "hint"]):
        """Checks the CWL file against all relevant OGC requirements.

        Parameters
        ----------
        include : list[str]
            A list of detail levels to be included in the output
            (possible values: 'error', 'hint', 'note')

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        valid = True
        issues = []

        res, out, err = self.validate_cwl()
        if res == 0:
            checks = [
                self.check_req_7,
                self.check_req_8,
                self.check_req_9,
                self.check_req_10,
                self.check_req_11,
                self.check_req_12,
                self.check_req_13,
                self.check_req_14,
                self.check_unsupported_cwl,
            ]
            for check in checks:
                sub_issues = check()
                if "error" in [i["type"] for i in sub_issues]:
                    valid = False

                issues.extend([i for i in sub_issues if i["type"] in include])
        else:
            valid = False
            if "error" in include:
                issues.append(
                    {"type": "error", "message": f"CWL is invalid; error message:\n{out}", "req": None}
                )

        return {
            "valid": valid,
            "issues": issues,
            "requirements": {
                r: AppPackage.requirement_specs[r] for r in set([i["req"] for i in issues if i["req"]])
            },
        }

    def check_req_7(self):
        """Checks the CWL file against OGC requirement 7 (minimum root elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        if not self.workflows:
            issues.append({"type": "error", "message": "No Workflow class defined", "req": "req-7"})

        if not self.command_line_tools:
            issues.append(
                {"type": "error", "message": "No CommandLineTool class defined", "req": "req-7"}
            )

        return issues

    def check_req_8(self):
        """Checks the CWL file against OGC requirement 8
        (CommandLineTool required elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []
        clt_count = 0
        for clt in self.command_line_tools:
            clt_count += 1
            if clt.id:
                clt_id = clt.id.split("#", 1)[-1]
                clt_name = f"CommandLineTool '{clt_id}'"
            else:
                clt_name = f"CommandLineTool #{clt_count}"
                issues.append(
                    {"type": "error", "message": f"Missing element for {clt_name}: id", "req": "req-8"}
                )

            for attribute in ["baseCommand", "inputs", "requirements"]:
                if getattr(clt, attribute, None) is None:
                    issues.append(
                        {
                            "type": "error",
                            "message": f"Missing element for {clt_name}: {attribute}",
                            "req": "req-8",
                        }
                    )

            requirements = []
            if clt.requirements:
                requirements.extend(clt.requirements)
            if clt.hints:
                requirements.extend(clt.hints)

            docker_requirement = next(
                (r for r in requirements if type(r).__name__.endswith("DockerRequirement")), None
            )
            if not docker_requirement or not docker_requirement.dockerPull:
                issues.append(
                    {
                        "type": "error",
                        "message": f"Missing element for {clt_name}: "
                        "requirements.DockerRequirement.dockerPull or "
                        "hints.DockerRequirement.dockerPull",
                        "req": "req-8",
                    }
                )

        return issues

    def check_req_9(self):
        """Checks the CWL file against OGC requirement 9
        (Workflow required elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        workflows = [self.workflow] if self.workflow else self.workflows

        wf_count = 0
        for workflow in workflows:
            wf_count += 1
            if workflow.id:
                wf_id = workflow.id.split("#", 1)[-1]
                wf_name = f"Workflow '{wf_id}'"
            else:
                wf_name = f"Workflow #{wf_count}"
                issues.append(
                    {"type": "error", "message": f"Missing element for {wf_name}: id", "req": "req-9"}
                )
            for attribute in ["label", "doc"]:
                if getattr(workflow, attribute, None) is None:
                    issues.append(
                        {
                            "type": "error",
                            "message": f"Missing element for {wf_name}: {attribute}",
                            "req": "req-9",
                        }
                    )

        return issues

    def check_req_10(self):
        """Checks the CWL file against OGC requirement 10
        (Workflow input required elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        workflows = [self.workflow] if self.workflow else self.workflows

        wf_count = 0
        for workflow in workflows:
            wf_count += 1
            if workflow.id:
                wf_id = workflow.id.split("#", 1)[-1]
                wf_name = f"Workflow '{wf_id}'"
            else:
                wf_name = f"Workflow #{wf_count}"

            input_count = 0
            for input in workflow.inputs:
                input_count += 1
                if input.id:
                    input_id = input.id.split("#", 1)[-1].split("/")[-1]
                    input_name = f"input '{input_id}'"
                else:
                    wf_name = f"input #{input_count}"
                    issues.append(
                        {
                            "type": "error",
                            "message": f"Missing element for {input_name} of {wf_name}: id",
                            "req": "req-10",
                        }
                    )

                for attribute in ["label", "doc"]:
                    if getattr(input, attribute, None) is None:
                        issues.append(
                            {
                                "type": "error",
                                "message": f"Missing element for {input_name} of {wf_name}: "
                                f"{attribute}",
                                "req": "req-10",
                            }
                        )
        return issues

    def check_req_11(self):
        """Checks the CWL file against OGC requirement 11
        (Additional metadata, required and optional elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        namespaces = (
            self.cwl["$namespaces"]
            if "$namespaces" in self.cwl and isinstance(self.cwl["$namespaces"], dict)
            else {}
        )
        schema_org_prefix = next((p for p in namespaces if namespaces[p] == "https://schema.org/"), None)

        has_version = False
        for attr in ["softwareVersion", "version"]:
            fq_attr = "{0}:{1}".format(schema_org_prefix, attr) if schema_org_prefix else None
            if fq_attr and fq_attr in self.cwl:
                has_version = True

        if not has_version:
            issues.append(
                {
                    "type": "error",
                    "message": "Missing metadata element for application package: softwareVersion",
                    "req": "req-11",
                }
            )

        for attr in [
            "author",
            "citation",
            "codeRepository",
            "contributor",
            "dateCreated",
            "keywords",
            "license",
            "releaseNotes",
        ]:
            fq_attr = "{0}:{1}".format(schema_org_prefix, attr) if schema_org_prefix else None
            if fq_attr and fq_attr not in self.cwl:
                issues.append(
                    {
                        "type": "note",
                        "message": f"Missing optional metadata element for application package: {attr}",
                        "req": "req-11",
                    }
                )

        return issues

    def check_req_12(self):
        """Checks the CWL file against OGC requirement 12
        (CommandLineTool input of type Directory).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        clt_count = 0
        for clt in self.command_line_tools:
            clt_count += 1
            if clt.id:
                clt_id = clt.id.split("#", 1)[-1]
                clt_name = f"CommandLineTool '{clt_id}'"
            else:
                clt_name = f"CommandLineTool #{clt_count}"

            has_directory = bool([i for i in clt.inputs if i.type == "Directory"])
            if not has_directory:
                issues.append(
                    {
                        "type": "hint",
                        "message": f"No input of type 'Directory' for {clt_name}; make sure inputs "
                        "referencing GeoJSON features of EO products that need to be staged in "
                        "are of type 'Directory'",
                        "req": "req-12",
                    }
                )

        return issues

    def check_req_13(self):
        """Checks the CWL file against OGC requirement 13
        (Workflow input of type Directory).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        workflows = [self.workflow] if self.workflow else self.workflows

        wf_count = 0
        for workflow in workflows:
            wf_count += 1
            if workflow.id:
                wf_id = workflow.id.split("#", 1)[-1]
                wf_name = f"Workflow '{wf_id}'"
            else:
                wf_name = f"Workflow #{wf_count}"

            has_directory = bool([i for i in workflow.inputs if i.type == "Directory"])
            if not has_directory:
                issues.append(
                    {
                        "type": "hint",
                        "message": f"No input of type 'Directory' for {wf_name}; make sure inputs "
                        "referencing GeoJSON features of EO products that need to be staged in "
                        "are of type 'Directory'",
                        "req": "req-13",
                    }
                )

        return issues

    def check_req_14(self):
        """Checks the CWL file against OGC requirement 14
        (CommandLineTool and Workflow output of type Directory).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """
        issues = []

        clt_count = 0
        for clt in self.command_line_tools:
            clt_count += 1
            if clt.id:
                clt_id = clt.id.split("#", 1)[-1]
                clt_name = f"CommandLineTool '{clt_id}'"
            else:
                clt_name = f"CommandLineTool #{clt_count}"

            has_directory = bool([i for i in clt.outputs if i.type == "Directory"])
            if not has_directory:
                issues.append(
                    {
                        "type": "hint",
                        "message": f"No output of type 'Directory' for {clt_name}; make sure "
                        "CommandLineTool outputs that need to be staged are of type 'Directory'",
                        "req": "req-14",
                    }
                )

        workflows = [self.workflow] if self.workflow else self.workflows

        wf_count = 0
        for workflow in workflows:
            wf_count += 1
            if workflow.id:
                wf_id = workflow.id.split("#", 1)[-1]
                wf_name = f"Workflow '{wf_id}'"
            else:
                wf_name = f"Workflow #{wf_count}"

            has_directory = bool([i for i in workflow.outputs if i.type == "Directory"])
            if not has_directory:
                issues.append(
                    {
                        "type": "hint",
                        "message": f"No output of type 'Directory' for {wf_name}; make sure "
                        "Workflow outputs that need to be staged out are of type 'Directory'",
                        "req": "req-14",
                    }
                )

        return issues

    def check_unsupported_cwl(self):
        """Checks the CWL file against OGC requirement 8
        (unsupported DockerRequirement elements).

        Returns
        -------
        list[dict]
            A list with encountered issues (can be empty)
        """

        issues = []

        for clt in self.command_line_tools:

            clt_id = clt.id.split("#", 1)[-1]
            clt_name = f"CommandLineTool '{clt_id}'"

            requirements = []
            if clt.requirements:
                requirements.extend(clt.requirements)
            if clt.hints:
                requirements.extend(clt.hints)

            docker_requirement = next(
                (r for r in requirements if type(r).__name__.endswith("DockerRequirement")), None
            )

            if docker_requirement and docker_requirement.dockerOutputDirectory:

                issues.append(
                    {
                        "type": "error",
                        "message": f"Unsupported element in DockerRequirement of {clt_name}: "
                        "'dockerOutputDirectory'",
                        "req": None,
                    }
                )

        return issues
