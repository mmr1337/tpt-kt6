import base64
import json
from pathlib import Path
from uuid import uuid4

import allure
import pytest
import requests

from base_request import BaseRequest
from models import Inventory


CASES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/6ZkAAAAASUVORK5CYII=")


@pytest.fixture
def api():
    with requests.Session() as session:
        session.headers["Accept"] = "application/json"
        yield BaseRequest("https://petstore.swagger.io/v2", session)


@pytest.fixture
def values():
    token = uuid4().hex[:12]
    return {"$id": int(token, 16) + 1000, "$name": f"tpt_{token}", "$email": f"tpt_{token}@example.invalid"}


def fill(value, values):
    if isinstance(value, str):
        if value in values:
            return values[value]
        for key, replacement in values.items():
            value = value.replace(key, str(replacement))
    elif isinstance(value, dict):
        return {key: fill(item, values) for key, item in value.items()}
    elif isinstance(value, list):
        return [fill(item, values) for item in value]
    return value


def send(api, scenario):
    arguments = {to: scenario[key] for key, to in (("json", "json"), ("query", "params"), ("form", "data")) if key in scenario}
    if scenario.get("upload"):
        arguments["files"] = {"file": ("pixel.png", PNG, "image/png")}
    if "accept" in scenario:
        arguments["headers"] = {"Accept": scenario["accept"]}
    return api._request(scenario["method"], scenario["path"], **arguments)


def assert_status(response, expected):
    assert response.status_code in expected, f"Ожидалось {expected}, получено {response.status_code}: {response.text[:350]}"


def verify_body(response, case):
    if case.get("checks"):
        body = response.json()
        for key, value in case["checks"].items():
            assert body[key] == value
    kind = case.get("kind")
    if kind == "inventory":
        Inventory.model_validate_json(response.content)
    elif kind == "message":
        assert response.json()["message"]
    elif kind in ("array", "available"):
        body = response.json()
        assert isinstance(body, list)
        if kind == "available":
            assert all(pet["status"] == "available" for pet in body)


def parameter(case):
    severity = allure.severity_level.CRITICAL if case["scenario"] == "positive" else allure.severity_level.NORMAL
    return pytest.param(
        case,
        id=f"{case['operation']}-{case['scenario']}",
        marks=[allure.feature(case["feature"]), allure.story(case["operation"]), allure.severity(severity)],
    )


@allure.title("Petstore · {param_id}")
@pytest.mark.parametrize("case", [parameter(case) for case in CASES])
def test_petstore(api, case, values):
    case = fill(case, values)
    try:
        if "setup" in case:
            assert_status(send(api, case["setup"]), [200])
        if case.get("login"):
            assert_status(api._request("GET", "user/login", params={"username": values["$name"], "password": "course-example-42"}), [200])
        response = send(api, case)
        assert_status(response, case["status"])
        if "follow" in case:
            response = api.get(case["follow"])
            assert_status(response, [200])
        verify_body(response, case)
        if "missing" in case:
            assert_status(api.get(case["missing"]), [404])
    finally:
        if "cleanup" in case:
            assert_status(api.delete(case["cleanup"]), [200, 404])
