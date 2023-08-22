import unittest
import json
from io import StringIO
from ap_validator.app_package import AppPackage


class TestCommandLineInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def validate_cwl_file(self, cwl_url, entry_point=None, detail="errors", format="json"):
        if "/" not in cwl_url:
            cwl_url = "/workspaces/app-package-validation/tests/data/{0}".format(cwl_url)
        out = StringIO()
        err = StringIO()
        res = AppPackage.process_cli(
            cwl_url, entry_point=entry_point, detail=detail, format=format, stdout=out, stderr=err
        )
        print(out.getvalue())
        out_r = json.loads(out.getvalue()) if format == "json" else out.getvalue()
        return res, out_r, err.getvalue()

    def test_cwl_missing(self):
        res, out, err = self.validate_cwl_file("missing.cwl")
        self.assertEqual(res, 2)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error" and "Missing or invalid" in i["message"]
                ]
            )
        )

    def test_cwl_invalid(self):
        res, out, err = self.validate_cwl_file("invalid.cwl")
        self.assertEqual(res, 2)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error" and "Did not recognise v1.8 as a CWL version" in i["message"]
                ]
            )
        )

    def test_cwl_req_7_no_wf(self):
        res, out, err = self.validate_cwl_file("req_7_no_wf.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error" and "No Workflow class defined" in i["message"]
                ]
            )
        )

    def test_cwl_req_7_no_clt(self):
        res, out, err = self.validate_cwl_file("req_7_no_clt.cwl")
        self.assertEqual(res, 1)
        # Not checking for message because CWL is invalid for reasons
        # other than the missing CommandLineTool (basic CWL validity
        # is impossible if CommandLineTool is missing since any Workflow
        # must have some direct or indirect reference to a CommandLineTool

    def test_cwl_req_8_no_clt_basecommand(self):
        res, out, err = self.validate_cwl_file("req_8_no_clt_basecommand.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error"
                    and i["message"] == "Missing element for CommandLineTool 'crop': baseCommand"
                ]
            )
        )

    def test_cwl_req_8_no_clt_dockerrequirement(self):
        res, out, err = self.validate_cwl_file("req_8_no_clt_dockerrequirement.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error"
                    and i["message"] == "Missing element for CommandLineTool 'crop': "
                    "requirements.DockerRequirement.dockerPull or hints.DockerRequirement.dockerPull"
                ]
            )
        )

    def test_cwl_req_9_no_wf_title(self):
        res, out, err = self.validate_cwl_file("req_9_no_wf_title.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error"
                    and i["message"] == "Missing element for Workflow 'water_bodies': label"
                ]
            )
        )

    def test_cwl_req_10_no_wf_input_abstract(self):
        res, out, err = self.validate_cwl_file("req_10_no_wf_input_abstract.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error"
                    and i["message"]
                    == "Missing element for input 'epsg' of Workflow 'water_bodies': doc"
                ]
            )
        )

    def test_cwl_req_11_no_version(self):
        res, out, err = self.validate_cwl_file("req_11_no_version.cwl")
        self.assertEqual(res, 1)
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error"
                    and i["message"]
                    == "Missing metadata element for application package: softwareVersion"
                ]
            )
        )

    def test_cwl_req_12_13_no_input_directory(self):
        res, out, err = self.validate_cwl_file("req_12_13_no_input_directory.cwl", detail="hints")
        self.assertEqual(res, 0)
        self.assertEqual(
            sum(
                [
                    1
                    for i in out["issues"]
                    if i["type"] == "hint"
                    and i["message"].startswith("No input of type 'Directory' for ")
                ]
            ),
            6,
        )

    def test_cwl_req_12_13_input_directory(self):
        res, out, err = self.validate_cwl_file("req_12_13_input_directory.cwl", detail="hints")
        self.assertEqual(res, 0)
        self.assertEqual(
            sum(
                [
                    1
                    for i in out["issues"]
                    if i["type"] == "hint"
                    and i["message"].startswith("No input of type 'Directory' for ")
                ]
            ),
            3,
        )

    def test_cwl_req_14_no_output_directory(self):
        res, out, err = self.validate_cwl_file("req_14_no_output_directory.cwl", detail="hints")
        self.assertEqual(res, 0)
        self.assertEqual(
            sum(
                [
                    1
                    for i in out["issues"]
                    if i["type"] == "hint"
                    and i["message"].startswith("No output of type 'Directory' for ")
                ]
            ),
            6,
        )

    def test_cwl_req_14_output_directory(self):
        res, out, err = self.validate_cwl_file("req_14_output_directory.cwl", detail="hints")
        self.assertEqual(res, 0)
        self.assertEqual(
            sum(
                [
                    1
                    for i in out["issues"]
                    if i["type"] == "hint"
                    and i["message"].startswith("No output of type 'Directory' for ")
                ]
            ),
            4,
        )

    def test_cwl_valid(self):
        res, out, err = self.validate_cwl_file("valid.cwl", detail="all")
        self.assertEqual(res, 0)
        self.assertEqual(sum([1 for i in out["issues"] if i["type"] == "error"]), 0)
        self.assertEqual(sum([1 for i in out["issues"] if i["type"] == "hint"]), 10)
        self.assertEqual(sum([1 for i in out["issues"] if i["type"] == "note"]), 8)
