import os
import smtplib, ssl
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for

# If your folders are literally named "templates" and "static", you can omit these args.
app = Flask(__name__, template_folder="templates", static_folder="static")

# ---------- Email helper (optional) ----------
def send_alert_email(subject: str, body: str) -> None:
    """
    Sends an email via SMTP if all required env vars are present.
    Required env vars:
      - SMTP_HOST
      - SMTP_USER
      - SMTP_PASS
      - ALERT_TO_EMAIL  (who receives alerts)
    Optional:
      - SMTP_PORT (defaults 587)
      - FROM_EMAIL (defaults to SMTP_USER)
    """
    to_email  = os.getenv("ALERT_TO_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("FROM_EMAIL", smtp_user or "noreply@undergroundheat.local")

    # Skip silently if not configured
    if not (to_email and smtp_host and smtp_user and smtp_pass):
        print("[EMAIL] Skipping (missing SMTP env vars).")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
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

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def home():
    # Renders templates/home.html
    return render_template("home.html")

@app.route("/submit", methods=["GET"])
def submit_get():
    # Renders templates/form.html
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit_post():
    # Minimal fields that match your current form.html
    artist_name = (request.form.get("artist_name") or "").strip()
    email       = (request.form.get("email") or "").strip()
    video_link  = (request.form.get("video_link") or "").strip()

    # Send an alert email (optional)
    body = f"""New submission received:

Artist: {artist_name or "-"}
Email:  {email or "-"}
Video:  {video_link or "-"}
"""
    try:
        send_alert_email("New Underground Heat submission", body)
        print("[EMAIL] Submission alert attempted.")
    except Exception as e:
        print("[EMAIL] Failed to send alert:", e)

    # Show success page
    return redirect(url_for("success"))

@app.route("/success", methods=["GET"])
def success():
    # Renders templates/success.html
    return render_template("success.html")

# Quick health check for Render
@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok"

# Manual SMTP test (visiting this tries to send a test email)
@app.route("/email-test", methods=["GET"])
def email_test():
    try:
        send_alert_email("Underground Heat — Email Test", "If you see this, SMTP works.")
        return "Sent ✅"
    except Exception as e:
        return f"Failed ❌: {e}", 500

# Local dev only; Render uses gunicorn with `app:app`
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
