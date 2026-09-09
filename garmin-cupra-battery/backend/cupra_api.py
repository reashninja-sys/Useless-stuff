"""
Cupra/SEAT Connected Services API client.

Uses the VW Group OAuth2 form-based login flow. The client IDs and endpoints
are reverse-engineered from the MyCupra app. VW Group rotates them without
notice — if auth breaks, check the seatconnect project for updated values:
https://github.com/rennecd/python-seatconnect

To override the client_id without editing this file, set CUPRA_CLIENT_ID
in your .env.
"""

import os
import re
import time
import logging
import secrets
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)

IDENTITY_BASE    = "https://identity.vwgroup.io"
CUPRA_API_BASE   = os.environ.get(
    "CUPRA_API_BASE",
    "https://ola.prod.code.seat.cloud.vwgroup.com",
)
CUPRA_REDIRECT_URI = "cupra://oauth-callback"
CUPRA_SCOPE        = "openid profile address email phone mbb offline_access cars vin"

# Known client IDs, newest first. We try them in order.
# Override all of them by setting CUPRA_CLIENT_ID in .env.
_KNOWN_CLIENT_IDS: List[str] = [
    os.environ.get("CUPRA_CLIENT_ID", ""),        # user override (may be empty string)
    "3c756d51-694f-4ef8-b2f4-c9f1f8e9d235",       # MyCupra (recent)
    "50f215ac-4444-4230-9fb1-1af6acbb6aba",        # SEAT/Cupra (older)
    "d381f117-9884-4e6e-9d56-e7b5e2ba4d52",        # SEAT Connect
]
CUPRA_CLIENT_IDS = [c for c in _KNOWN_CLIENT_IDS if c]  # drop empty

REQUEST_TIMEOUT = 30  # seconds


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
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-GB,en;q=0.9",
        })
        self.access_token:  Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry:  float = 0
        self._client_id:    Optional[str] = None  # whichever ID worked

    def _is_token_valid(self) -> bool:
        return self.access_token is not None and time.time() < self.token_expiry - 60

    # ------------------------------------------------------------------ auth

    def authenticate(self) -> None:
        """Try each known client ID until one succeeds."""
        last_error: Optional[Exception] = None
        for cid in CUPRA_CLIENT_IDS:
            try:
                logger.debug("Trying client_id %s", cid)
                self._authenticate_with(cid)
                self._client_id = cid
                logger.info("Authenticated with client_id %s", cid)
                return
            except CupraAuthError as e:
                last_error = e
                logger.debug("client_id %s failed: %s", cid, e)
                # Reset session cookies before next attempt
                self.session.cookies.clear()

        raise CupraAuthError(
            f"Authentication failed with all known client IDs. "
            f"Last error: {last_error}"
        )

    def _authenticate_with(self, client_id: str) -> None:
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)

        auth_params = {
            "client_id":     client_id,
            "response_type": "code",
            "scope":         CUPRA_SCOPE,
            "redirect_uri":  CUPRA_REDIRECT_URI,
            "state":         state,
            "nonce":         nonce,
        }
        auth_url = f"{IDENTITY_BASE}/oidc/v1/authorize?{urlencode(auth_params)}"

        # Step 1: load login page
        resp = self.session.get(auth_url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        self._check_not_error_page(resp, "loading login page")

        form_data = self._extract_hidden_fields(resp.text)
        if not form_data:
            raise CupraAuthError(
                f"No form fields found on login page (client_id {client_id} may be invalid). "
                f"Page title: {self._page_title(resp.text)!r}"
            )
        identifier_url = self._signin_url(resp.url, client_id, "login/identifier")

        # Step 2: submit email
        form_data.update({"email": self.username, "registerFlow": "false"})
        resp = self.session.post(
            identifier_url, data=form_data,
            allow_redirects=True, timeout=REQUEST_TIMEOUT,
        )
        self._check_not_error_page(resp, "submitting email")
        self._check_not_wrong_password(resp)

        form_data2 = self._extract_hidden_fields(resp.text)
        authenticate_url = self._signin_url(resp.url, client_id, "login/authenticate")

        # Step 3: submit password
        form_data2.update({
            "email":        self.username,
            "password":     self.password,
            "registerFlow": "false",
        })
        resp = self.session.post(
            authenticate_url, data=form_data2,
            allow_redirects=False, timeout=REQUEST_TIMEOUT,
        )

        # Step 4: chase redirects to find auth code
        code = self._follow_for_code(resp, client_id)
        if not code:
            # Try to give a useful hint
            body_snippet = resp.text[:400].lower()
            if "wrong" in body_snippet or "invalid" in body_snippet or "incorrect" in body_snippet:
                raise CupraAuthError("Wrong email or password.")
            if "two-factor" in body_snippet or "2fa" in body_snippet or "mfa" in body_snippet:
                raise CupraAuthError(
                    "Two-factor authentication is enabled. "
                    "Disable it in the MyCupra app and retry."
                )
            raise CupraAuthError(
                f"Could not obtain authorization code (client_id={client_id}). "
                "Check credentials or MFA."
            )

        # Step 5: exchange code for tokens
        token_resp = self.session.post(
            f"{IDENTITY_BASE}/oidc/v1/token",
            data={
                "grant_type":   "authorization_code",
                "code":         code,
                "redirect_uri": CUPRA_REDIRECT_URI,
                "client_id":    client_id,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if not token_resp.ok:
            raise CupraAuthError(
                f"Token exchange failed {token_resp.status_code}: {token_resp.text[:200]}"
            )
        self._store_tokens(token_resp.json())

    def refresh_access_token(self) -> None:
        if not self.refresh_token or not self._client_id:
            self.authenticate()
            return

        resp = self.session.post(
            f"{IDENTITY_BASE}/oidc/v1/token",
            data={
                "grant_type":    "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id":     self._client_id,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if not resp.ok:
            logger.warning("Token refresh failed (%s), re-authenticating", resp.status_code)
            self.authenticate()
            return
        self._store_tokens(resp.json())
        logger.debug("Token refreshed")

    def ensure_authenticated(self) -> None:
        if not self._is_token_valid():
            if self.refresh_token:
                self.refresh_access_token()
            else:
                self.authenticate()

    # ------------------------------------------------------------------ API

    def get_battery_status(self) -> Dict[str, Any]:
        """Fetch battery/charge status from the Cupra connected services API."""
        self.ensure_authenticated()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept":        "application/json",
        }
        url = f"{CUPRA_API_BASE}/v2/vehicles/{self.vin}/status"

        resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 401:
            logger.info("401 on vehicle status — re-authenticating")
            self.authenticate()
            headers["Authorization"] = f"Bearer {self.access_token}"
            resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        if not resp.ok:
            raise CupraAPIError(
                f"Vehicle status failed {resp.status_code}. "
                f"Response: {resp.text[:300]}"
            )

        payload = resp.json()
        logger.debug("Raw API response keys: %s", list(payload.keys()))
        result = self._parse_battery(payload)

        if result["battery_level"] is None:
            logger.warning(
                "Battery level not found in response. Full payload:\n%s",
                payload,
            )

        return result

    # ------------------------------------------------------------------ helpers

    def _store_tokens(self, tokens: dict) -> None:
        self.access_token  = tokens["access_token"]
        self.refresh_token = tokens.get("refresh_token", self.refresh_token)
        self.token_expiry  = time.time() + tokens.get("expires_in", 3600)

    def _extract_hidden_fields(self, html: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for tag in re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.I):
            name  = re.search(r'name=["\']([^"\']+)["\']', tag)
            value = re.search(r'value=["\']([^"\']*)["\']', tag)
            if name:
                fields[name.group(1)] = value.group(1) if value else ""
        return fields

    def _signin_url(self, current_url: str, client_id: str, step: str) -> str:
        parsed = urlparse(current_url)
        m = re.search(r"/signin-service/v1/([^/]+)/", parsed.path)
        cid = m.group(1) if m else client_id
        return f"{IDENTITY_BASE}/signin-service/v1/{cid}/{step}"

    def _follow_for_code(
        self, resp: requests.Response, client_id: str
    ) -> Optional[str]:
        for _ in range(20):
            if resp.status_code not in (301, 302, 303, 307, 308):
                break
            location = resp.headers.get("Location", "")
            if not location:
                break
            parsed = urlparse(location)
            params = parse_qs(parsed.query)
            if "code" in params:
                return params["code"][0]
            if "error" in params:
                raise CupraAuthError(
                    f"Auth server returned error: {params.get('error_description', params['error'])}"
                )
            resp = self.session.get(
                location, allow_redirects=False, timeout=REQUEST_TIMEOUT
            )

        # Last-resort scan of body
        m = re.search(r"[?&]code=([^&\"'\s]+)", resp.text)
        return m.group(1) if m else None

    def _check_not_error_page(self, resp: requests.Response, step: str) -> None:
        if not resp.ok:
            raise CupraAuthError(
                f"HTTP {resp.status_code} when {step}. "
                f"Page: {self._page_title(resp.text)!r}"
            )

    def _check_not_wrong_password(self, resp: requests.Response) -> None:
        lower = resp.text.lower()
        if any(w in lower for w in ("wrong password", "invalid credentials", "incorrect password")):
            raise CupraAuthError("Wrong email or password.")

    @staticmethod
    def _page_title(html: str) -> str:
        m = re.search(r"<title>([^<]+)</title>", html, re.I)
        return m.group(1).strip() if m else "(no title)"

    def _parse_battery(self, data: dict) -> Dict[str, Any]:
        """
        VW Group API response shape has changed repeatedly.
        We probe multiple known layouts so the code survives API updates.
        """
        result: Dict[str, Any] = {
            "battery_level": None,
            "range_km":      None,
            "charging":      False,
            "charging_state": None,
        }

        vehicle = data.get("data", data)

        # ── Shape A: batteryStatus (Cupra Born / VW ID / most EVs) ────────────
        bat = vehicle.get("batteryStatus", {})
        if bat:
            result["battery_level"] = bat.get("currentSoc_pct")
            result["range_km"]      = bat.get("cruisingRangeElectric_km")
            state = bat.get("chargingStatus", "")
            result["charging"]      = state.upper() in ("CHARGING", "CONSERVATION")
            result["charging_state"] = state
            return result

        # ── Shape B: fuelStatus.rangeStatus (older API versions) ──────────────
        primary = (
            vehicle
            .get("fuelStatus", {})
            .get("rangeStatus", {})
            .get("primaryEngine", {})
        )
        if primary:
            result["battery_level"] = primary.get("currentSoc_pct")
            result["range_km"]      = primary.get("remainingRange_km")
            return result

        # ── Shape C: electric.batteryStatus (some newer endpoints) ────────────
        elec = vehicle.get("electric", {})
        if elec:
            result["battery_level"] = elec.get("soc")
            result["range_km"]      = elec.get("range")
            charge = elec.get("charging", {})
            result["charging"]      = charge.get("active", False)
            return result

        # ── Shape D: flat currentFuelLevel (non-EV / PHEV fallback) ──────────
        fuel = vehicle.get("currentFuelLevel", {})
        if fuel:
            result["battery_level"] = fuel.get("value")
            return result

        logger.warning(
            "Battery level not found. Top-level keys: %s  vehicle keys: %s",
            list(data.keys()), list(vehicle.keys()),
        )
        return result
