#!/usr/bin/env python3
"""
Run this FIRST in Termux to confirm Cupra auth and API work
before starting the full server.

Usage:
    cd garmin-cupra-battery/backend
    python3 test_cupra.py
"""
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # will read from env directly

# ── check config ──────────────────────────────────────────────────────────────

print("=" * 52)
print("  Cupra API connectivity test")
print("=" * 52)
print()
print("Checking .env …")

def _show(var, secret=False):
    val = os.environ.get(var)
    if not val:
        print(f"  ✗  {var}  — NOT SET")
        return None
    display = ("*" * max(0, len(val) - 4) + val[-4:]) if secret else val
    print(f"  ✓  {var} = {display}")
    return val

username = _show("CUPRA_USERNAME")
password = _show("CUPRA_PASSWORD", secret=True)
vin      = _show("CUPRA_VIN")
_show("API_KEY", secret=True)
print()

if not all([username, password, vin]):
    print("Fix the above in .env and re-run.")
    sys.exit(1)

from cupra_api import CupraClient, CupraAuthError, CupraAPIError

client = CupraClient(username, password, vin)

# ── step 1: auth ──────────────────────────────────────────────────────────────

print("Step 1/2  Authenticating with Cupra …")
t0 = time.time()
try:
    client.authenticate()
    ttl = int(client.token_expiry - time.time())
    print(f"  ✓  OK in {time.time()-t0:.1f}s  (token valid for {ttl}s)")
except CupraAuthError as e:
    print(f"  ✗  {e}")
    print()
    print("Common causes:")
    print("  • Wrong email or password")
    print("  • 2FA / MFA enabled on your account — disable it in the MyCupra app")
    print("  • VW Group rotated the client_id — check CUPRA_CLIENT_ID in cupra_api.py")
    print("    and compare with: https://github.com/rennecd/python-seatconnect")
    sys.exit(1)

# ── step 2: fetch data ────────────────────────────────────────────────────────

print()
print("Step 2/2  Fetching battery status …")
t0 = time.time()
try:
    data = client.get_battery_status()
    print(f"  ✓  OK in {time.time()-t0:.1f}s")
    print()
    print("  Battery level : ", data["battery_level"], "%")
    print("  Range         : ", data["range_km"], "km")
    print("  Charging      : ", data["charging"])
    print("  Charge state  : ", data["charging_state"])
except CupraAPIError as e:
    print(f"  ✗  {e}")
    print()
    print("The raw API URL we're calling is stored in CUPRA_API_BASE in cupra_api.py.")
    print("If you see a 404, the endpoint path may have changed.")
    sys.exit(1)

print()
print("=" * 52)
print("  All good — run:  bash start.sh")
print("=" * 52)
