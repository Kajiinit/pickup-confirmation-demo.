# Pickup Confirmation Demo

A standalone local Flask demo. It is separate from OnlyEarn and uses its own SQLite database (`submissions.db`).

## What it does
- Shows a pickup-address confirmation form.
- Saves the address submitted, the IP address seen by the server, submission time, browser user-agent, and referring website host where available.
- Offers optional browser geolocation. Coordinates are sent only after the visitor presses the location button and grants browser permission.
- Provides a password-protected admin dashboard at `/admin`.

## Privacy and location limitations
- The form explains what information is collected before submission.
- IP geolocation is not included in this first version. IP addresses generally indicate an approximate network location, not an exact street address.
- Device coordinates require explicit browser permission and work only in supported contexts (normally localhost or HTTPS).
- Behind a reverse proxy, `request.remote_addr` may be the proxy's IP. Do not blindly trust `X-Forwarded-For`; configure trusted proxy handling for the actual hosting provider before deploying.
- This demo is for local testing. Before public deployment, add CSRF protection, login throttling, a stronger production session configuration, HTTPS, retention/deletion controls, and a proper privacy notice.

## Run on macOS
Open Terminal and enter the extracted folder, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_PASSWORD='replace-with-a-long-unique-password'
python app.py
```

Open http://127.0.0.1:5055

Admin login: http://127.0.0.1:5055/admin/login

Use the password set in `ADMIN_PASSWORD`. Do not use a real password you use elsewhere. Keep this demo private until production hardening is complete.

## Stop the server
Press `Control+C` in Terminal.
