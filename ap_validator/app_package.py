import os
import tempfile
from io import StringIO
from typing import Dict
from urllib.parse import urlparse

import requests
import yaml

from cwl_utils.parser import load_document as load_cwl
from cwltool.main import main
from loguru import logger
from requests.exceptions import InvalidSchema


class AppPackageValidationException(Exception):
    def __init__(self, message, req_text=None):
        self.message = message
        self.req_text = req_text
        super().__init__(self.message)


class AppPackage:
    REQ_7_TEXT = """The Application Package SHALL be a valid CWL document with a "Workflow" class """
    """and one or more "CommandLineTool" classes"""
    REQ_8_TEXT = """The Application Package CWL CommandLineTool classes SHALL contain """
    """the following elements:"""
    """Identifier ("id"); Command line name ("baseCommand"); """
    """Input parameters ("inputs"); Environment requirements ("requirements"); """
    """Docker information ("DockerRequirement")"""
    REQ_9_TEXT = """The Application Package CWL Workflow class SHALL contain the following elements: """
    """Identifier ("id"); Title ("label"); Abstract ("doc")"""
    REQ_10_TEXT = """The Application Package CWL Workflow class “inputs” fields SHALL contain """
    """the following elements: Identifier ("id"); Title ("label"); Abstract ("doc")"""
    REQ_11_TEXT = """The Application Package CWL Workclass classes SHALL include additional metadata """
    """as defined in Table 1 ("author", "citation", "codeRepository", "contributor", """
    """"dateCreated", "keywords", "license", "releaseNotes", "version")"""

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
    def from_string(cls, cwl_str, entry_point=None):
        cwl_obj = yaml.safe_load(cwl_str)

        return cls(cwl=cwl_obj, entry_point=entry_point)

    @classmethod
    def from_url(cls, url):
        try:
            cwl_content = yaml.safe_load(requests.get(url).text)
        except InvalidSchema:
            parsed_url = urlparse(url)
            with open(os.path.abspath(parsed_url.path)) as f:
                cwl_content = yaml.safe_load(f)

        return cls(cwl=cwl_content)

    def validate_cwl(self):
        temp_dir = tempfile.mkdtemp()
        with open(os.path.join(temp_dir, "temp_cwl"), "w") as outfile:
            yaml.dump(self.cwl, outfile, default_flow_style=False)

        out = StringIO()
        err = StringIO()
        res = main(
            ["--validate", os.path.join(temp_dir, "temp_cwl")],
            stderr=out,
            stdout=err,
        )

        return res, out.getvalue(), err.getvalue()

    def check_req_7(self):
        issues = []

        if not self.workflows:
            issues.append({"type": "error", "message": "No Workflow class defined", "req": "req-8"})

        if not self.command_line_tools:
            issues.append(
                {"type": "error", "message": "No CommandLineTool class defined", "req": "req-8"}
            )

        return issues

    def check_req_8(self):
        # checks CLI dockerRequirement
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
                    input_name = f"input '{input.id}'"
                else:
                    wf_name = f"input #{input_count}"
                    issues.append(
                        {
                            "type": "error",
                            "message": f"Missing element for {input_name} of {wf_name}': id",
                            "req": "req-10",
                        }
                    )

                for attribute in ["label", "doc"]:
                    if getattr(input, attribute, None) is None:
                        issues.append(
                            {
                                "type": "error",
                                "message": f"Missing element for {input_name} of {wf_name}':"
                                f"{attribute}",
                                "req": "req-10",
                            }
                        )
        return issues

    def check_req_11(self):
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

            for attribute in ["version"]:
                if getattr(workflow, attribute, None) is None:
                    issues.append(
                        {
                            "type": "error",
                            "message": f"Missing element for {wf_name}: {attribute}",
                            "req": "req-11",
                        }
                    )

            for attribute in [
                "author",
                "citation",
                "codeRepository",
                "contributor",
                "dateCreated",
                "keywords",
                "license",
                "releaseNotes",
            ]:
                if getattr(workflow, attribute, None) is None:
                    issues.append(
                        {
                            "type": "hint",
                            "message": f"Missing optional element for {wf_name}: {attribute}",
                            "req": "req-11",
                        }
                    )

        return issues

    def check_req_12(self):
        return []

    def check_req_13(self):
        return []

    def check_req_14(self):
        return []

    def check_unsupported_cwl(self):
        """checks for unsupported CWL requirements"""
        detected_wrong_elements = set()

        for clt in [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]:

            for req in clt.hints + clt.requirements:

                if "DockerRequirement" in str(req):

                    dockerOutputDirectory = req.dockerOutputDirectory

                    if dockerOutputDirectory:
                        detected_wrong_elements.add("dockerOutputDirectory")
                        logger.error(
                            f"for {clt.id}: Requirement 'dockerOutputDirectory'"
                            " is not supported in DockerRequirement."
                        )

        if len(detected_wrong_elements) > 0:
            raise AppPackageValidationException(
                "Requirement 'dockerOutputDirectory' is not" " supported in DockerRequirement."
            )
