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
    pass


class AppPackage:
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

        try:
            # TODO add check: one or more “CommandLineTool” classes.
            assert workflows
        except AssertionError:
            raise AppPackageValidationException(
                "The Application Package SHALL be a valid CWL document with a Workflow class (...)"
            )

    def check_req_8(self, entrypoint):
        # checks CLI dockerRequirement
        clts = [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]
        missing_clt_elements = []
        docker_requirements = ["DockerRequirement"]  # baseCommand, inputs, requirements, id
        for clt in clts:
            clt_id = clt.id
            clt_id_split = clt_id.split("#")[1]
            if entrypoint and clt_id.split("#")[1] != entrypoint:
                continue
            for docker_requirement in docker_requirements:
                try:
                    if not any([docker_requirement in str(req) for req in clt.requirements]) and not any(
                        [docker_requirement in str(req) for req in clt.hints]
                    ):
                        missing_clt_elements.append(clt_id)
                        logger.error(
                            f"For {clt_id_split}: The Application Package CWL CommandLineTool"
                            " class SHALL contain the following nested elements:"
                            " 'hints' / 'DockerRequirement' -> 'dockerPull'"
                        )
                except Exception as exc:
                    missing_clt_elements.append(clt_id_split)
                    logger.error(
                        f"{exc} for {clt_id_split}: The Application Package CWL "
                        " CommandLineTool class SHALL contain the following"
                        " nested elements: 'hints' / 'DockerRequirement' -> 'dockerPull'"
                    )
        if len(clts) > 0 and len(missing_clt_elements) > 0:
            raise AppPackageValidationException(
                "The Application Package CWL CommandLineTool"
                " class SHALL contain the following nested elements:"
                " 'hints' / 'DockerRequirement' -> 'dockerPull'. "
                f"Missing element{'s' if len(missing_clt_elements)>1 else ''}:"
                f" {' '.join(missing_clt_elements)}"
            )

    def check_req_9(self, entrypoint):
        workflows = [item for item in self.cwl_obj if item.class_ == "Workflow"]
        workflow = next((wf for wf in workflows if wf.id.split("#")[1] == entrypoint), None)

        missing_wf_elements = []
        attributes = ["id", "label", "doc"]
        for attribute in attributes:
            try:
                assert getattr(workflow, attribute, None) is not None
            except AssertionError:
                missing_wf_elements.append(attribute)

        if missing_wf_elements:
            raise AppPackageValidationException(
                "The Application Package CWL Workflow class SHALL"
                f" contain the following elements: {attributes}. "
                "Missing element{'s' if len(missing_wf_elements)>1"
                " else ''}: {' '.join(missing_wf_elements)}"
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
                            f"Input '{input.id.split('#')[1]}' element" "'{attribute}' is not set\n"
                        )

            if missing_wf_inputs_elements:
                raise AppPackageValidationException(
                    "The Application Package CWL Workflow class "
                    "inputs fields SHALL contain the following "
                    f"elements: {attributes}.\n  {'; '.join(missing_wf_inputs_elements)}"
                )

    def check_unsupported_cwl(self, entrypoint):
        """checks for unsupported CWL requirements"""
        clts = [item for item in self.cwl_obj if item.class_ == "CommandLineTool"]
        detected_wrong_elements = set()
        for clt in clts:
            if entrypoint and clt.id.split("#")[1] != entrypoint:
                continue
            clt_id = clt.id
            reqs_n_hints = []
            if clt.hints:
                reqs_n_hints = clt.hints
            if clt.requirements:
                reqs_n_hints = reqs_n_hints + clt.requirements
            for req in reqs_n_hints:
                req_str = str(req)
                # print(f"req_str {req_str}")
                if "DockerRequirement" in req_str:
                    dockerOutputDirectory = req.dockerOutputDirectory
                    # print(f"dockerOutputDirectory {dockerOutputDirectory}")
                    if dockerOutputDirectory:
                        detected_wrong_elements.add("dockerOutputDirectory")
                        logger.error(
                            f"for {clt_id}: Requirement 'dockerOutputDirectory'"
                            " is not supported in DockerRequirement."
                        )

        if len(clts) > 0 and len(detected_wrong_elements) > 0:
            raise AppPackageValidationException(
                "Requirement 'dockerOutputDirectory' is not"
                " supported in DockerRequirement."
            )
