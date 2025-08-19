import os
from flask import Flask, request, redirect, url_for, render_template
from jinja2 import TemplateNotFound

# If your folders are named "Templates" / "Static" (capitalized), Flask on Linux is case-sensitive.
# This makes Flask look in either lowercase or capitalized folders.
TEMPLATE_DIR = "templates" if os.path.isdir("templates") else ("Templates" if os.path.isdir("Templates") else None)
STATIC_DIR   = "static"   if os.path.isdir("static")   else ("Static"   if os.path.isdir("Static")   else None)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# --------- Helpers: safe render with fallback HTML ----------
def render_or_fallback(template_name: str, fallback_html: str, **ctx):
    try:
        if app.template_folder:
            return render_template(template_name, **ctx)
        raise TemplateNotFound(template_name)
    except TemplateNotFound:
        return fallback_html

# ---------------------- Routes ------------------------------
@app.route("/")
def home():
    return render_or_fallback(
        "home.html",
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Underground Heat</title></head>
  <body style="font-family:Arial; padding:24px;">
    <h1>Underground Heat — It works! 🔥</h1>
    <p>Your Flask app is running on Render.</p>
    <ul>
      <li><a href="/submit">Submit form</a></li>
      <li><a href="/email-test">Email test route</a></li>
      <li><a href="/healthz">Health check</a></li>
    </ul>
    <p>(Once you add real templates, this page will automatically use them.)</p>
  </body>
</html>"""
    )

@app.route("/submit", methods=["GET"])
def submit_get():
    return render_or_fallback(
        "form.html",
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Submit | Underground Heat</title></head>
  <body style="font-family:Arial; padding:24px;">
    <h2>Artist Submission (demo form)</h2>
    <form method="post" action="/submit">
      <div><label>Artist Name <input name="artist_name" required></label></div>
      <div><label>Email <input type="email" name="email" required></label></div>
      <div><label>Video Link <input name="video_link" required></label></div>
      <button type="submit">Send</button>
    </form>
    <p><a href="/">← Back</a></p>
  </body>
</html>"""
    )

@app.route("/submit", methods=["POST"])
def submit_post():
    # For this first deploy we’ll just accept the data and show a Thank You.
    # (We’ll wire DB + email next.)
    artist = request.form.get("artist_name", "").strip()
    print("[FORM] Received submission from:", artist or "(no name)")
    return redirect(url_for("success"))

@app.route("/success")
def success():
    return render_or_fallback(
        "success.html",
        """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Success</title></head>
  <body style="font-family:Arial; padding:24px;">
    <h2>Thank you! ✅</h2>
    <p>Your info was received.</p>
    <p><a href="/">Go home</a></p>
  </body>
</html>"""
    )

@app.route("/email-test")
def email_test():
    # Placeholder so the route exists and proves routing is good.
    # We’ll hook this up to SendGrid once the base app is live.
    return """Email test route is live. (Not sending yet — we’ll wire SMTP next.)"""

@app.route("/healthz")
def healthz():
    return "ok"

# --------------- Dev server (ignored by gunicorn) ---------------
if __name__ == "__main__":
    # Local run: python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
