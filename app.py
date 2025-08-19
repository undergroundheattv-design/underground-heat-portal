import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from flask import Flask, render_template, request, abort

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = Flask(__name__)

# -----------------------------------------------------------------------------
# Email helper
# -----------------------------------------------------------------------------
def send_email(subject: str, body: str, to_email: str | None = None) -> None:
    """
    Sends an email via SMTP using environment variables:

      SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS
      ALERT_TO_EMAIL (fallback 'to'), FROM_EMAIL (optional), REPLY_TO (optional)

    If required env vars are missing, it will just log and skip.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    default_to = os.getenv("ALERT_TO_EMAIL")
    to_addr = (to_email or default_to)
    if not (smtp_host and smtp_user and smtp_pass and to_addr):
        print("[EMAIL] Skipping (missing SMTP_HOST/USER/PASS or recipient).")
        return

    from_addr = os.getenv("FROM_EMAIL", smtp_user)
    reply_to = os.getenv("REPLY_TO")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    timeout = 20
    if smtp_port == 465:  # SMTPS
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=timeout) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    else:  # STARTTLS
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as s:
            s.ehlo()
            s.starttls(context=context)
            s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html", current_year=datetime.now().year)

@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html", current_year=datetime.now().year)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        message = (request.form.get("message") or "").strip()

        body = f"""New contact form submission

Name: {name or '-'}
Email: {email or '-'}
Message:
{message or '-'}
"""
        try:
            # Sends to ALERT_TO_EMAIL unless you pass to_email=email
            send_email("New Contact — Underground Heat", body, to_email=None)
            return render_template("contact.html", success=True, current_year=datetime.now().year)
        except Exception as e:
            print("[EMAIL] contact send failed:", e)
            return render_template("contact.html", error=True, current_year=datetime.now().year)

    return render_template("contact.html", current_year=datetime.now().year)

@app.route("/privacy", methods=["GET"])
def privacy():
    return render_template(
        "privacy.html",
        current_year=datetime.now().year,
        effective_date=os.getenv("PRIVACY_EFFECTIVE", "August 2025"),
    )

@app.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html", current_year=datetime.now().year)

@app.route("/admin", methods=["GET"])
def admin():
    """
    Simple gate: require ?key=<ADMIN_PASSWORD> in the query string.
    Set ADMIN_PASSWORD in Render env. Defaults to 'changeme'.
    """
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")
    if request.args.get("key") != admin_password:
        return abort(401)

    rows = []  # placeholder for future DB rows
    return render_template("admin.html", rows=rows, current_year=datetime.now().year)

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok"

@app.route("/email-test", methods=["GET"])
def email_test():
    try:
        send_email("Email Test — Underground Heat", "If you see this, SMTP works.")
        return "Sent ✅"
    except Exception as e:
        print("[EMAIL-TEST] Failed:", e)
        return f"Failed ❌: {e}", 500

# -----------------------------------------------------------------------------
# Local dev entrypoint (Render uses: gunicorn app:app)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
