import os
import smtplib, ssl
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for
from jinja2 import TemplateNotFound

# Detect template/static folder names (handles Templates/Static too)
TEMPLATE_DIR = "templates" if os.path.isdir("templates") else ("Templates" if os.path.isdir("Templates") else None)
STATIC_DIR   = "static"   if os.path.isdir("static")   else ("Static"   if os.path.isdir("Static")   else None)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

def render_or_fallback(template_name: str, fallback_html: str, **ctx):
    try:
        if app.template_folder:
            return render_template(template_name, **ctx)
        raise TemplateNotFound(template_name)
    except TemplateNotFound:
        # Show a minimal inline page instead of 500
        return fallback_html

def send_alert_email(subject: str, body: str) -> None:
    """Optional SMTP alert (skips quietly if not configured)."""
    to_email  = os.getenv("ALERT_TO_EMAIL")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("FROM_EMAIL", smtp_user or "noreply@undergroundheat.local")

    if not (to_email and smtp_host and smtp_user and smtp_pass):
        print("[EMAIL] Skipping send (missing SMTP env vars).")
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

@app.route("/", methods=["GET"])
def home():
    return render_or_fallback(
        "home.html",
        """<!doctype html><html><body style="font-family:Arial;padding:24px">
        <h1>Underground Heat — It works 🔥</h1>
        <ul>
          <li><a href="/submit">Submit form</a></li>
          <li><a href="/email-test">Email test</a></li>
          <li><a href="/healthz">Health</a></li>
        </ul>
        <p>(Showing fallback because templates/home.html not found.)</p>
        </body></html>"""
    )

@app.route("/submit", methods=["GET"])
def submit_get():
    return render_or_fallback(
        "form.html",
        """<!doctype html><html><body style="font-family:Arial;padding:24px">
        <h2>Artist Submission (fallback)</h2>
        <form method="post" action="/submit">
          <div><label>Artist Name <input name="artist_name" required></label></div>
          <div><label>Email <input type="email" name="email" required></label></div>
          <div><label>Video Link <input name="video_link" required></label></div>
          <button type="submit">Send</button>
        </form>
        <p><a href="/">← Back</a></p>
        </body></html>"""
    )

@app.route("/submit", methods=["POST"])
def submit_post():
    artist_name = (request.form.get("artist_name") or "").strip()
    email       = (request.form.get("email") or "").strip()
    video_link  = (request.form.get("video_link") or "").strip()

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

    return redirect(url_for("success"))

@app.route("/success", methods=["GET"])
def success():
    return render_or_fallback(
        "success.html",
        """<!doctype html><html><body style="font-family:Arial;padding:24px;text-align:center">
        <h2>Thank you! ✅</h2>
        <p>Your submission was received.</p>
        <p><a href="/">Go home</a></p>
        <p>(Showing fallback because templates/success.html not found.)</p>
        </body></html>"""
    )

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok"

@app.route("/email-test", methods=["GET"])
def email_test():
    try:
        send_alert_email("Underground Heat — Email Test", "If you see this, SMTP works.")
        return "Sent ✅"
    except Exception as e:
        return f"Failed ❌: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
from flask import abort

@app.route("/privacy")
def privacy():
    return render_template(
        "privacy.html",
        last_updated="August 2025",
        contact_email=os.getenv("CONTACT_EMAIL", "info@undergroundheat.tv"),
    )

@app.route("/terms")
def terms():
    return render_template(
        "terms.html",
        last_updated="August 2025",
        contact_email=os.getenv("CONTACT_EMAIL", "info@undergroundheat.tv"),
    )

@app.route("/admin")
def admin():
    # Simple password check: visit /admin?key=YOUR_PASSWORD
    admin_key = os.getenv("ADMIN_PASSWORD", "changeme")
    if (request.args.get("key") or "") != admin_key:
        return abort(401)
    # If you don’t have a DB wired yet, keep rows empty:
    rows = []
    return render_template("admin.html", rows=rows)
