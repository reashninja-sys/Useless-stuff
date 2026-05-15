# Garmin Cupra Battery Widget

Displays your Cupra EV's battery state-of-charge on a **Garmin vivoactive 4** (or 4S).

```
  ┌─────────────────────────────┐
  │           CUPRA             │
  │                             │
  │            82%              │
  │  [████████████████░░░░]     │
  │        320 km range         │
  │         Charging            │
  │      Updated 14:32          │
  └─────────────────────────────┘
```

Battery colour: green > 60 %, yellow 20–60 %, red < 20 %.  
Tap the screen or press the select button to force a refresh.

---

## Architecture

```
Garmin vivoactive 4
  └─ HTTP GET /battery
         │
   Python backend server   ←→   Cupra / VW Group API
   (runs on your home server       (OAuth2 + vehicle status)
    or Raspberry Pi)
```

The watch polls your backend every 5 minutes.  
The backend caches the result and only contacts Cupra's servers when the cache expires (default 5 min), keeping auth token refreshes to a minimum.

---

## 1. Backend Setup

### Requirements
- Python 3.10+
- A machine on your home network that is always on (Pi, NAS, old laptop, etc.)
  - Or any cloud VM / free-tier service if you want remote access

### Install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
nano .env                      # fill in your Cupra credentials + VIN
```

Your VIN is on your V5C, in the MyCupra app (Settings → Vehicle), or inside the driver's door jamb.

### Run

```bash
python server.py
```

Test it from another device on the same network:
```
curl http://YOUR_SERVER_IP:5000/battery
```

Expected response:
```json
{
  "battery_level": 82,
  "range_km": 320,
  "charging": false,
  "charging_state": "NOT_READY_FOR_CHARGING",
  "last_updated": "14:32"
}
```

### Run as a service (systemd)

```ini
# /etc/systemd/system/cupra-battery.service
[Unit]
Description=Cupra Battery API
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/garmin-cupra-battery/backend
EnvironmentFile=/home/pi/garmin-cupra-battery/backend/.env
ExecStart=/home/pi/garmin-cupra-battery/backend/.venv/bin/gunicorn server:app -b 0.0.0.0:5000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now cupra-battery
```

---

## 2. Garmin Widget Setup

### Requirements
- [Connect IQ SDK](https://developer.garmin.com/connect-iq/sdk/) 4.x
- Garmin Connect Mobile app (to sideload and configure the widget)

### Build

```bash
cd widget
monkeyc -o CupraBattery.prg \
        -f monkey.jungle \
        -y /path/to/developer_key.der \
        -d vivoactive4
```

Or use the **Connect IQ** extension for VS Code (right-click `monkey.jungle` → Build).

### Sideload to your watch

```bash
monkeydo CupraBattery.prg vivoactive4
```

Or use the Garmin Connect IQ app (simulator) or transfer via USB.

### Configure the Server URL

1. Open **Garmin Connect Mobile** on your phone
2. Go to your vivoactive 4 → **Widget Settings** → **Cupra Battery**
3. Set **Server URL** to `http://YOUR_SERVER_IP:5000`
   - Use your server's LAN IP if you're only using this at home
   - Use a public URL (with HTTPS!) if you want it to work away from home

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "Set Server URL" on watch | Garmin Connect settings not saved yet |
| "No connection" on watch | Watch can't reach server; check Wi-Fi, IP, firewall |
| "Server error" on watch | Check server logs — usually a Cupra auth failure |
| Auth fails on first run | Wrong credentials, or MFA is enabled on your Cupra account |
| `battery_level` is `null` | API response shape changed; check `cupra_api.py` `_parse_battery` and update field names |
| 401 on every request | Client ID rotated by VW Group; update `CUPRA_CLIENT_ID` in `cupra_api.py` |

### Checking for API changes

The Cupra API is not public. VW Group rotates client IDs and endpoint paths periodically.
If auth breaks, check these community resources for updated credentials:

- [python-seatconnect on GitHub](https://github.com/rennecd/python-seatconnect) (search for `CLIENT_ID`)
- Home Assistant `seatconnect` integration discussions

### MFA / Two-Factor Authentication

The current auth flow does not support interactive MFA. If your account has MFA enabled,
disable it in the MyCupra app, or create a dedicated account with read-only access via
Cupra's family sharing feature.

---

## Files

```
garmin-cupra-battery/
├── backend/
│   ├── cupra_api.py      # Cupra OAuth client + battery data parser
│   ├── server.py         # Flask HTTP server
│   ├── requirements.txt
│   └── .env.example      # copy to .env and fill in
└── widget/
    ├── manifest.xml       # targets vivoactive4 and vivoactive4s
    ├── monkey.jungle
    ├── source/
    │   ├── CupraBatteryApp.mc
    │   ├── CupraBatteryView.mc   # all drawing + HTTP logic
    │   └── CupraBatteryDelegate.mc
    └── resources/
        ├── drawables/
        ├── strings/
        └── settings/
            ├── properties.xml    # default ServerUrl
            └── settings.xml      # Garmin Connect settings UI
```
