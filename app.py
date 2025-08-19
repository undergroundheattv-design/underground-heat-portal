import os
from datetime import datetime
import smtplib, ssl
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, abort
from jinja2 import TemplateNotFound

# If your folders are named exactly "templates" and "static", this is fine:
app = Flask(__name__, template_folder="templates", static_folder="static")

# -------- helpers --------
def render_or_fallback(template_name: str, fallback_html: str, **ctx):
    """Try to render a Jinja template; if it's missing, use simple fallback HTML."""
    try:
        return render_template(template_name, **ctx)
    except TemplateNotFound:
        return fallback_html

def send_alert_email(subject: str, body: str) -> None:
    """Send an email via SMTP if env vars are present (optional)."""
    to_email  = os.getenv("ALERT_TO_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("FROM_EMAIL", smtp_user or "noreply@undergroundheat.local")

    if not (to_email and smtp_host and smtp_user and smtp_pass):
        print("[EMAIL] Skipping send — missing SMTP env vars.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    # Optional Reply-To
    if os.getenv("REPLY_TO"):
        msg["Reply-To"] = os.getenv("REPLY_TO")
    msg.set_content(body)

    timeout = 20
    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=timeout) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
            context = ssl.create_default_context()
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

# -------- routes --------
@app.route("/")
def home():
    return render_template("home.html", current_year=datetime.now().year)

@app.route("/submit", methods=["GET"])
def submit_get():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit_post():
    artist = (request.form.get("artist_name") or "").strip()
    email  = (request.form.get("email") or "").strip()
    video  = (request.form.get("video_link") or "").strip()

    body = f"""New submission received:

Artist: {artist or "-"}
Email:  {email or "-"}
Video:  {video or "-"}
"""
    try:
        send_alert_email("New Underground Heat submission", body)
        print("[EMAIL] Submission alert sent (or skipped if not configured).")
    except Exception as e:
        print("[EMAIL] Failed to send alert:", e)

    return redirect(url_for("success"))

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", last_updated="August 2025")

@app.route("/terms")
def terms():
    return render_template("terms.html", last_updated="August 2025")

@app.route("/admin")
def admin():
    # simple key gate
    if request.args.get("key") != os.getenv("ADMIN_PASSWORD", "changeme"):
        return abort(401)
    # You can add real data later; for now just render the page.
    return render_template("admin.html")

@app.route("/email-test")
def email_test():
    try:
        send_alert_email("Underground Heat — Email Test", "If you see this, SMTP works.")
        return "Sent ✅"
    except Exception as e:
        return f"Failed ❌: {e}", 500

@app.route("/healthz")
def healthz():
    return "ok"

# -------- local run --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
