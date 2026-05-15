"""
Cupra/SEAT Connected Services API client.

Uses the VW Group OAuth2 form-based login flow (same infrastructure as
Skoda, SEAT, Cupra). The client_id and endpoints are reverse-engineered
from the MyCupra app — check the seatconnect project on GitHub if they stop
working after a VW Group API rotation.
"""

import re
import time
import logging
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode, urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)

# MyCupra app OAuth credentials (may need updating after VW Group rotations)
CUPRA_CLIENT_ID = "3c756d51-694f-4ef8-b2f4-c9f1f8e9d235"
CUPRA_REDIRECT_URI = "cupra://oauth-callback"
CUPRA_SCOPE = "openid profile address email phone mbb offline_access cars vin"

IDENTITY_BASE = "https://identity.vwgroup.io"
CUPRA_API_BASE = "https://ola.prod.code.seat.cloud.vwgroup.com"


class CupraAuthError(Exception):
    pass


class CupraAPIError(Exception):
    pass


class CupraClient:
    def __init__(self, username: str, password: str, vin: str):
        self.username = username
        self.password = password
        self.vin = vin
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Accept": "application/json",
            "Accept-Language": "en-GB",
        })
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: float = 0

    def _is_token_valid(self) -> bool:
        return self.access_token is not None and time.time() < self.token_expiry - 60

    def authenticate(self) -> None:
        """Perform VW Group OAuth2 form-based authentication."""
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)

        auth_params = {
            "client_id": CUPRA_CLIENT_ID,
            "response_type": "code",
            "scope": CUPRA_SCOPE,
            "redirect_uri": CUPRA_REDIRECT_URI,
            "state": state,
            "nonce": nonce,
        }
        auth_url = f"{IDENTITY_BASE}/oidc/v1/authorize?{urlencode(auth_params)}"

        # Step 1: Load the login page (follows redirects to sign-in form)
        resp = self.session.get(auth_url, allow_redirects=True)
        resp.raise_for_status()

        form_data = self._extract_hidden_fields(resp.text)
        identifier_url = self._signin_url(resp.url, "login/identifier")

        # Step 2: Submit email address
        form_data.update({"email": self.username, "registerFlow": "false"})
        resp = self.session.post(identifier_url, data=form_data, allow_redirects=True)
        resp.raise_for_status()

        form_data2 = self._extract_hidden_fields(resp.text)
        authenticate_url = self._signin_url(resp.url, "login/authenticate")

        # Step 3: Submit password (don't auto-follow so we can grab the code)
        form_data2.update({
            "email": self.username,
            "password": self.password,
            "registerFlow": "false",
        })
        resp = self.session.post(authenticate_url, data=form_data2, allow_redirects=False)

        # Step 4: Chase redirects manually to capture the authorization code
        code = self._follow_for_code(resp)
        if not code:
            raise CupraAuthError(
                "Could not obtain authorization code. "
                "Check your credentials or whether MFA is enabled on your account."
            )

        # Step 5: Exchange code for tokens
        token_resp = self.session.post(
            f"{IDENTITY_BASE}/oidc/v1/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CUPRA_REDIRECT_URI,
                "client_id": CUPRA_CLIENT_ID,
            },
        )
        token_resp.raise_for_status()
        self._store_tokens(token_resp.json())
        logger.info("Cupra authentication successful")

    def refresh_access_token(self) -> None:
        if not self.refresh_token:
            self.authenticate()
            return

        resp = self.session.post(
            f"{IDENTITY_BASE}/oidc/v1/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": CUPRA_CLIENT_ID,
            },
        )
        if resp.status_code != 200:
            logger.warning("Token refresh failed, re-authenticating")
            self.authenticate()
            return
        self._store_tokens(resp.json())

    def ensure_authenticated(self) -> None:
        if not self._is_token_valid():
            if self.refresh_token:
                self.refresh_access_token()
            else:
                self.authenticate()

    def get_battery_status(self) -> Dict[str, Any]:
        """Fetch battery/charge status from the Cupra API."""
        self.ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{CUPRA_API_BASE}/v2/vehicles/{self.vin}/status"

        resp = self.session.get(url, headers=headers)
        if resp.status_code == 401:
            self.authenticate()
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = self.session.get(url, headers=headers)

        if not resp.ok:
            raise CupraAPIError(f"Vehicle status request failed: {resp.status_code} {resp.text[:200]}")

        return self._parse_battery(resp.json())

    # ------------------------------------------------------------------ helpers

    def _store_tokens(self, tokens: dict) -> None:
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens.get("refresh_token", self.refresh_token)
        self.token_expiry = time.time() + tokens.get("expires_in", 3600)

    def _extract_hidden_fields(self, html: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for tag in re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.I):
            name = re.search(r'name=["\']([^"\']+)["\']', tag)
            value = re.search(r'value=["\']([^"\']*)["\']', tag)
            if name:
                fields[name.group(1)] = value.group(1) if value else ""
        return fields

    def _signin_url(self, current_url: str, step: str) -> str:
        parsed = urlparse(current_url)
        m = re.search(r"/signin-service/v1/([^/]+)/", parsed.path)
        client_id = m.group(1) if m else CUPRA_CLIENT_ID
        return f"{IDENTITY_BASE}/signin-service/v1/{client_id}/{step}"

    def _follow_for_code(self, resp: requests.Response) -> Optional[str]:
        for _ in range(15):
            if resp.status_code not in (301, 302, 303, 307, 308):
                break
            location = resp.headers.get("Location", "")
            parsed = urlparse(location)
            params = parse_qs(parsed.query)
            if "code" in params:
                return params["code"][0]
            resp = self.session.get(location, allow_redirects=False)

        # Last-resort: look for code= in the body
        m = re.search(r"[?&]code=([^&\"'\s]+)", resp.text)
        return m.group(1) if m else None

    def _parse_battery(self, data: dict) -> Dict[str, Any]:
        """
        The VW Group API response format has changed across versions.
        We try multiple known shapes so this keeps working across updates.
        """
        result: Dict[str, Any] = {
            "battery_level": None,
            "range_km": None,
            "charging": False,
            "charging_state": None,
        }

        vehicle = data.get("data", data)

        # Shape A: batteryStatus (Cupra Born, most EVs)
        bat = vehicle.get("batteryStatus", {})
        if bat:
            result["battery_level"] = bat.get("currentSoc_pct")
            result["range_km"] = bat.get("cruisingRangeElectric_km")
            state = bat.get("chargingStatus", "")
            result["charging"] = state.upper() in ("CHARGING", "CONSERVATION")
            result["charging_state"] = state
            return result

        # Shape B: fuelStatus.rangeStatus.primaryEngine (older API)
        primary = (
            vehicle
            .get("fuelStatus", {})
            .get("rangeStatus", {})
            .get("primaryEngine", {})
        )
        if primary:
            result["battery_level"] = primary.get("currentSoc_pct")
            result["range_km"] = primary.get("remainingRange_km")
            return result

        # Shape C: currentFuelLevel (non-EV fallback)
        fuel = vehicle.get("currentFuelLevel", {})
        if fuel:
            result["battery_level"] = fuel.get("value")
            return result

        logger.warning("Unrecognised API response shape: %s", list(vehicle.keys()))
        return result
