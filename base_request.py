import json

import allure


class BaseRequest:
    def __init__(self, base_url, session):
        self.base_url = base_url.rstrip("/")
        self.session = session

    def _request(self, method, endpoint, **kwargs):
        with allure.step(f"{method} /{endpoint}"):
            url = f"{self.base_url}/{endpoint}"
            if "json" in kwargs:
                allure.attach(json.dumps(kwargs["json"]), "Тело запроса", allure.attachment_type.JSON)
            response = self.session.request(method, url, timeout=15, **kwargs)
            details = f"{response.request.method} {response.url}\nHTTP {response.status_code}"
            allure.attach(details, "HTTP", allure.attachment_type.TEXT)
            content_type = response.headers.get("Content-Type", "")
            kind = allure.attachment_type.JSON if "json" in content_type else allure.attachment_type.TEXT
            allure.attach(response.text, "Тело ответа", kind)
            return response

    def get(self, endpoint):
        return self._request("GET", endpoint)

    def post(self, endpoint, body):
        return self._request("POST", endpoint, json=body)

    def put(self, endpoint, body):
        return self._request("PUT", endpoint, json=body)

    def delete(self, endpoint):
        return self._request("DELETE", endpoint)
