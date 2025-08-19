from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # change this in production

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        artist_name = request.form['artist_name']
        email = request.form['email']
        video_link = request.form['video_link']
        cover_art = request.files.get('cover_art')

        filename = None
        if cover_art and cover_art.filename:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{cover_art.filename}"
            cover_art.save(os.path.join(UPLOAD_FOLDER, filename))

        # Save submission to CSV
        with open('submissions.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now(), artist_name, email, video_link, filename])

        return render_template('submit.html', message="Submission received!")
    return render_template('submit.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Save contact to CSV
        with open('messages.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now(), name, email, message])

        return render_template('contact.html', message="Message sent successfully!")
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
