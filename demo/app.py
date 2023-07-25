import json
import os
from urllib.parse import urlparse

import requests
import streamlit as st
import yaml
from ap_validator.app_package import AppPackage, AppPackageValidationException
from code_editor import code_editor
from cwl_utils.parser import load_document as load_cwl
from loguru import logger
from requests.exceptions import InvalidSchema

st.header("Application Package validator")

entrypoint = st.text_input(
    "Set the Application Package entry point:", value="water_bodies", key="entrypoint"
)

cwl_url = "https://github.com/Terradue/ogc-eo-application-package-hands-on/releases/download/1.1.7/app-water-bodies.1.1.7.cwl"  # noqa: E501,W505

with open(
    "/workspaces/app-package-validator/demo/resources/custom_buttons_bar_alt.json"
) as json_button_file_alt:
    custom_buttons_alt = json.load(json_button_file_alt)

try:
    cwl_content = requests.get(cwl_url).text
except InvalidSchema:
    parsed_url = urlparse(cwl_url)
    with open(os.path.abspath(parsed_url.path)) as f:
        cwl_content = yaml.safe_load(f)
        cwl_content = f.read()

btn_settings_editor_btns = [
    {
        "name": "copy",
        "feather": "Copy",
        "hasText": True,
        "alwaysOn": True,
        "commands": ["copyAll"],
        "style": {"top": "0rem", "right": "0.4rem"},
    },
    {
        "name": "update",
        "feather": "RefreshCw",
        "primary": True,
        "hasText": True,
        "showWithIcon": True,
        "commands": ["submit"],
        "style": {"bottom": "0rem", "right": "0.4rem"},
    },
]

height = [22, 25]
language = "yaml"
theme = "default"
shortcuts = "vscode"
focus = False
wrap = True
btns = custom_buttons_alt

ace_props = {"style": {"borderRadius": "0px 0px 8px 8px"}}
response_dict = code_editor(
    cwl_content,
    height=height,
    lang=language,
    theme=theme,
    shortcuts=shortcuts,
    focus=focus,
    buttons=btns,
    props=ace_props,
    options={"wrap": wrap},
    allow_reset=True,
    key="code_editor_demo",
)
logger.info(response_dict["type"])
if response_dict["type"] == "submit":
    cwl_content = response_dict["text"]

    ap = AppPackage.from_string(cwl_content)
    logger.info(response_dict.keys())

    res, out, err = ap.validate_cwl()
    logger.info(f"res: {res}")
    if res == 0:
        st.info("CWL is valid")
    else:
        st.error(err)

    valid = True

    cwl_obj = load_cwl(yaml.safe_load(cwl_content), load_all=True)

    try:
        ap.check_req_7()
    except AppPackageValidationException as e:
        st.error(e)
        valid = False

    try:
        ap.check_req_8(entrypoint=entrypoint)
    except AppPackageValidationException as e:
        st.error(e)
        valid = False

    try:
        ap.check_req_9(entrypoint=entrypoint)
    except AppPackageValidationException as e:
        st.error(e)
        valid = False

    try:
        ap.check_req_10(entrypoint=entrypoint)
    except AppPackageValidationException as e:
        st.error(e)
        valid = False

    try:
        ap.check_unsupported_cwl(entrypoint=entrypoint)
    except AppPackageValidationException as e:
        st.error(e)
        valid = False

    if valid:
        st.info(
            "CWL is compliant with the OGC's Best Practices for Earth Observation Application Packages"
        )
