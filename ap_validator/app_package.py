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
    """and one or more "CommandLineTool" classes."""
    REQ_8_TEXT = """The Application Package CWL CommandLineTool classes SHALL contain """
    """the following elements:"""
    """Identifier ("id"); Command line name ("baseCommand"); """
    """Input parameters ("inputs"); Environment requirements ("requirements"); """
    """Docker information ("DockerRequirement")"""
    REQ_9_TEXT = """The Application Package CWL Workflow class SHALL contain the following elements: """
    """Identifier ("id"); Title ("label"); Abstract ("doc")"""

    def __init__(self, cwl: Dict) -> None:

        self.cwl = cwl
        self.cwl_obj = load_cwl(cwl, load_all=True)

    @classmethod
    def from_string(cls, cwl_str):
        cwl_obj = yaml.safe_load(cwl_str)

        return cls(cwl=cwl_obj)

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

        workflows = [item for item in self.cwl_obj if item.class_ == "Workflow"]
        if not workflows:
            raise AppPackageValidationException(
                message="Workflow class missing", req_text=self.__class__.REQ_7_TEXT
            )

        command_line_tools = [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]
        if not command_line_tools:
            raise AppPackageValidationException(
                message="CommandLineTool class missing", req_text=self.__class__.REQ_7_TEXT
            )

    def check_req_8(self, entrypoint):
        # checks CLI dockerRequirement
        command_line_tools = [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]
        missing_elements = []
        clt_count = 0
        for clt in command_line_tools:
            clt_count += 1
            if clt.id:
                clt_parts = clt.id.split("#", 1)
                clt_id = clt_parts[1] if len(clt_parts) > 1 else clt.id
            else:
                clt_id = f"CommandLineTool #{clt_count}"
                missing_elements.append(f"id ({clt_id})")

            for attribute in ["baseCommand", "inputs", "requirements"]:
                if getattr(clt, attribute, None) is None:
                    missing_elements.append(f"{attribute} ({clt_id})")

            requirements = []
            if clt.requirements:
                print("REQ {0}: {1}".format(clt_id, type(clt.requirements)))
                for r in clt.requirements:
                    print("- REQ {0}: {1}".format(type(r), r.__dir__()))
                requirements.extend(clt.requirements)
            if clt.hints:
                print("HINT {0}: {1}".format(clt_id, type(clt.hints)))
                for h in clt.hints:
                    print("- REQ {0}: {1}".format(type(h), h.__dir__()))
                requirements.extend(clt.hints)

            # clt_id = clt.id
            # clt_id_split = clt_id.split("#")[1]
            # if entrypoint and clt_id.split("#")[1] != entrypoint:
            #    continue

            for r in requirements:
                print("TYPE: {0}".format(type(r).__name__))

            docker_requirement = next(
                (r for r in requirements if type(r).__name__.endswith("DockerRequirement")), None
            )
            if not docker_requirement or not docker_requirement.dockerPull:
                missing_elements.append(
                    "requirements.{0} or hints.{0} ({1})".format("DockerRequirement.dockerPull", clt_id)
                )

        if missing_elements > 0:
            raise AppPackageValidationException(
                "Missing CommandLineTool element{0}: {1}".format(
                    "" if len(missing_elements) == 1 else "s", ", ".join(missing_elements)
                ),
                self.__class__.REQ_8_TEXT,
            )

    def check_req_9(self, entrypoint):
        workflows = [item for item in self.cwl_obj if item.class_ == "Workflow"]
        workflow = next((wf for wf in workflows if wf.id.split("#")[1] == entrypoint), None)

        missing_elements = []
        for attribute in ["id", "label", "doc"]:
            if getattr(workflow, attribute, None) is None:
                missing_elements.append(attribute)

        if missing_elements > 0:
            raise AppPackageValidationException(
                "Missing Workflow element{0}: {1}".format(
                    "" if len(missing_elements) == 1 else "s", ", ".join(missing_elements)
                ),
                self.__class__.REQ_9_TEXT,
            )

    def check_req_10(self, entrypoint):
        # https://docs.ogc.org/bp/20-089r1.html#toc37
        workflows = [item for item in self.cwl_obj if item.class_ == "Workflow"]

        workflow = next((wf for wf in workflows if wf.id.split("#")[1] == entrypoint), None)
        if workflow:
            missing_wf_inputs_elements = []
            attributes = ["label", "doc"]
            for input in workflow.inputs:
                for attribute in attributes:
                    try:
                        assert getattr(input, attribute, None) is not None
                    except AssertionError:
                        missing_wf_inputs_elements.append(
                            f"Input '{input.id.split('#')[1]}' element '{attribute}' is not set\n"
                        )

            if missing_wf_inputs_elements:
                raise AppPackageValidationException(
                    "The Application Package CWL Workflow class "
                    "inputs fields SHALL contain the following "
                    f"elements: {attributes}.\n  {'; '.join(missing_wf_inputs_elements)}"
                )

    def check_unsupported_cwl(self, entrypoint):
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
