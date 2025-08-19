from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Underground Heat is Live!"

@app.route("/email-test")
def email_test():
    return "Email Test Page"

# This line is only used when running locally.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
