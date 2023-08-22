import unittest

from ap_validator.app_package import AppPackage
from loguru import logger


class TestCalrissianContext(unittest.TestCase):
    cwl_str = """
cwlVersion: v1.0
$graph:
- class: CommandLineTool
  id: stac
  requirements:
    InlineJavascriptRequirement: {}
    EnvVarRequirement:
        envDef:
          PATH: /bin
          PYTHONPATH: /home/jovyan/water-bodies/command-line-tools/stac
          PROJ_LIB: /opt/conda/envs/env_stac/lib/python3.9/site-packages/rasterio/proj_data
    ResourceRequirement:
        coresMax: 2
        ramMax: 2028
  hints:
    DockerRequirement:
        dockerPull: docker.terradue.com/wbd_stac:latest
  baseCommand: ["python", "-m", "app"]
  arguments: []
  inputs:
      item:
        type:
          type: array
          items: string
          inputBinding:
            prefix: --input-item
      rasters:
        type:
          type: array
          items: File
          inputBinding:
            prefix: --water-body
  outputs:
      stac_catalog:
        outputBinding:
          glob: .
        type: Directory

"""

    @classmethod
    def setUpClass(cls) -> None:

        cls.cwl_remote_url = "https://github.com/Terradue/ogc-eo-application-package-hands-on/releases/download/1.1.7/app-water-bodies.1.1.7.cwl"  # noqa: E501,W505
        cls.cwl_local_url = (
            "file:///workspaces/app-package-validation/water_bodies.1.1.6.cwl"  # noqa: E501,W505
        )
        cls.cwl_unsupported_url = "file:///workspaces/app-package-validation/tests/data/test_deny_unsupported.cwl"  # noqa: E501,W505

    def test_from_str(self):
        ap = AppPackage.from_string(cwl_str=TestCalrissianContext.cwl_str)
        self.assertIsInstance(ap, AppPackage)

    def test_from_localfile(self):

        ap = AppPackage.from_url(url=self.cwl_local_url)

        self.assertIsInstance(ap, AppPackage)

    def test_from_url(self):

        ap = AppPackage.from_url(url=self.cwl_remote_url)

        self.assertIsInstance(ap, AppPackage)

    def test_validate(self):

        ap = AppPackage.from_url(url=self.cwl_remote_url)

        res, out, err = ap.validate_cwl()

        logger.info(f"validate_cwl out:{out}")
        self.assertEqual(res, 0)
