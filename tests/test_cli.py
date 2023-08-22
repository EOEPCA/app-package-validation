import unittest
import json
from io import StringIO
from ap_validator.app_package import AppPackage


class TestCommandLineInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def validate_cwl_file(self, cwl_url, entry_point=None, detail=["error"], format="json"):
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
        self.assertEqual(res, 1)
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
        self.assertEqual(res, 1)
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
        self.assertTrue(
            bool(
                [
                    i
                    for i in out["issues"]
                    if i["type"] == "error" and "No CommandLineTool class defined" in i["message"]
                ]
            )
        )
