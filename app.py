import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "submissions.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set SECRET_KEY before running. See README.md.")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("Set ADMIN_PASSWORD before running. See README.md.")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT NOT NULL,
                pickup_address TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                referrer_host TEXT,
                latitude REAL,
                longitude REAL,
                location_shared INTEGER NOT NULL DEFAULT 0
            )
        """)

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    return response

@app.get("/")
def home():
    return render_template("pickup.html")

@app.post("/submit")
def submit():
    address = (request.form.get("pickup_address") or "").strip()
    if not address or len(address) > 500:
        flash("Please enter an address (up to 500 characters).", "error")
        return redirect(url_for("home"))

    lat = lon = None
    shared = 0
    try:
        raw_lat = request.form.get("latitude", "").strip()
        raw_lon = request.form.get("longitude", "").strip()
        if raw_lat and raw_lon:
            lat, lon = float(raw_lat), float(raw_lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                lat = lon = None
            else:
                shared = 1
    except ValueError:
        lat = lon = None

    # This demo records the direct peer address. Behind a reverse proxy it may
    # be the proxy's address; do not trust X-Forwarded-For without configuring
    # the trusted proxy chain for your actual hosting environment.
    ip = request.remote_addr
    referrer_host = None
    if request.referrer:
        from urllib.parse import urlparse
        referrer_host = urlparse(request.referrer).netloc[:255] or None

    with get_db() as db:
        db.execute("""
            INSERT INTO submissions
            (submitted_at, pickup_address, ip_address, user_agent, referrer_host,
             latitude, longitude, location_shared)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            address, ip, (request.user_agent.string or "")[:500],
            referrer_host, lat, lon, shared
        ))
    return render_template("thanks.html", location_shared=bool(shared))

@app.get("/admin/login")
def admin_login():
    return render_template("admin_login.html")

@app.post("/admin/login")
def admin_login_post():
    supplied = request.form.get("password", "")
    # Constant-time comparison avoids a simple timing leak.
    import hmac
    if hmac.compare_digest(supplied, ADMIN_PASSWORD):
        session.clear()
        session["is_admin"] = True
        return redirect(url_for("admin_dashboard"))
    flash("Incorrect password.", "error")
    return redirect(url_for("admin_login"))

@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.get("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        rows = db.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT 500").fetchall()
    return render_template("admin.html", rows=rows)

init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
