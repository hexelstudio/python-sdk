"""Token management — handles API key and client_credentials auth flows."""
from __future__ import annotations
import time
import httpx


class AuthManager:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        sts_url: str = "https://sts.hexelstudio.com",
    ):
        self._api_key = api_key
        self._client_id = client_id
        self._client_secret = client_secret
        self._sts_url = sts_url
        self._access_token: str | None = None
        self._expires_at: float = 0
        self._http = httpx.Client(timeout=10)

        if not api_key and not (client_id and client_secret):
            raise ValueError("Provide api_key or (client_id + client_secret)")

    @property
    def token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token
        self._refresh()
        return self._access_token

    def _refresh(self):
        if self._api_key:
            resp = self._http.post(
                f"{self._sts_url}/token",
                headers={"X-API-Key": self._api_key},
            )
        else:
            resp = self._http.post(
                f"{self._sts_url}/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 900)
