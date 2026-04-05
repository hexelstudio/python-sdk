"""HTTP request pipeline — retries, auth refresh, error handling."""
from __future__ import annotations
import time
import httpx
from hexel._internal.auth import AuthManager

RETRY_STATUS = {429, 500, 502, 503}
MAX_RETRIES = 3


class HttpClient:
    def __init__(self, *, base_url: str, auth: AuthManager, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._auth = auth
        self._client = httpx.Client(timeout=timeout)

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._auth.token}"
        headers.setdefault("Content-Type", "application/json")

        for attempt in range(MAX_RETRIES + 1):
            resp = self._client.request(method, url, headers=headers, **kwargs)
            if resp.status_code == 401 and attempt == 0:
                self._auth._refresh()
                headers["Authorization"] = f"Bearer {self._auth.token}"
                continue
            if resp.status_code in RETRY_STATUS and attempt < MAX_RETRIES:
                time.sleep(0.5 * (2 ** attempt))
                continue
            return resp
        return resp

    def get(self, path, **kw) -> httpx.Response:
        return self.request("GET", path, **kw)

    def post(self, path, **kw) -> httpx.Response:
        return self.request("POST", path, **kw)

    def put(self, path, **kw) -> httpx.Response:
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw) -> httpx.Response:
        return self.request("DELETE", path, **kw)

    def patch(self, path, **kw) -> httpx.Response:
        return self.request("PATCH", path, **kw)
