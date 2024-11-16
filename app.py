import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# File paths for storing data
USERS_FILE = 'data/users.json'
DIARY_FILE = 'data/diary.json'
NOTES_FILE = 'data/notes.json'
SETTINGS_FILE = 'data/settings.json'

# Admin credentials
ADMIN_USER = 'Amir'
ADMIN_PASS = '1962'

# Timezone choices (for simplicity, we’ll just list a few)
TIMEZONE_CHOICES = ['UTC', 'Asia/Tehran', 'America/New_York', 'Europe/London']

# Load users from the JSON file
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

# Load diary posts
def load_diary_posts():
    if not os.path.exists(DIARY_FILE):
        return []
    with open(DIARY_FILE) as f:
        return json.load(f)

# Save diary posts
def save_diary_posts(posts):
    with open(DIARY_FILE, 'w') as f:
        json.dump(posts, f, indent=4)

# Load notes from the JSON file
def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        return json.load(f)

# Save notes to the JSON file
def save_notes(notes):
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=4)

# Load user settings (language, timezone)
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE) as f:
        return json.load(f)

# Save user settings
def save_settings(username, settings):
    current_settings = load_settings()
    current_settings[username] = settings
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(current_settings, f, indent=4)

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        
        if username in users and users[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

# Diary route (View, Edit, Add, Delete)
@app.route('/diary', methods=['GET', 'POST'])
def diary():
    if 'username' not in session:
        return redirect(url_for('login'))

    posts = load_diary_posts()

    # Sort the posts by date (newest to oldest)
    posts.sort(key=lambda x: x['date'], reverse=True)

    if request.method == 'POST':
        # Only admin (Amir) can add or edit posts
        if session['username'] == ADMIN_USER:
            title = request.form['title']
            content = request.form['content']
            post_id = request.form.get('post_id')

            if post_id:  # Editing an existing post
                post = next((p for p in posts if p['id'] == post_id), None)
                if post:
                    post['title'] = title
                    post['content'] = content
                    post['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:  # Adding a new post
                new_post = {
                    'id': str(len(posts) + 1),  # Generate a unique ID
                    'title': title,
                    'content': content,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                posts.append(new_post)

            save_diary_posts(posts)  # Save posts after edit/add
            flash('Diary post saved successfully!', 'success')
            return redirect(url_for('diary'))

    # If user is not Amir, they can only view the diary
    return render_template('diary.html', username=session['username'], posts=posts, is_admin=session['username'] == ADMIN_USER)

# Delete a post (Admin only)
@app.route('/diary/delete/<post_id>')
def delete_post(post_id):
    if 'username' not in session or session['username'] != ADMIN_USER:
        return redirect(url_for('login'))

    posts = load_diary_posts()
    posts = [post for post in posts if post['id'] != post_id]  # Remove post by ID
    save_diary_posts(posts)
    flash('Diary post deleted successfully!', 'success')
    return redirect(url_for('diary'))

# Notes route (Send and receive notes)
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    notes = load_notes()

    # Sort the notes by timestamp (newest to oldest)
    notes.sort(key=lambda x: x['timestamp'], reverse=True)

    if request.method == 'POST':
        receiver = request.form['receiver']
        content = request.form['content']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Amir can send notes to anyone
        if session['username'] == ADMIN_USER:
            new_note = {
                'sender': username,
                'receiver': receiver,
                'content': content,
                'timestamp': timestamp
            }
            notes.append(new_note)
            save_notes(notes)
            flash('Note sent successfully!', 'success')
            return redirect(url_for('notes'))

        # Other users can only send notes to Amir
        elif session['username'] != ADMIN_USER and receiver == ADMIN_USER:
            new_note = {
                'sender': username,
                'receiver': receiver,
                'content': content,
                'timestamp': timestamp
            }
            notes.append(new_note)
            save_notes(notes)
            flash('Note sent to Amir!', 'success')
            return redirect(url_for('notes'))

        flash('You can only send notes to Amir!', 'danger')
        return redirect(url_for('notes'))

    # Filter notes to only show those sent to/from the logged-in user
    user_notes = [note for note in notes if note['receiver'] == username or note['sender'] == username]
    return render_template('notes.html', username=username, notes=user_notes)


# Settings route (Language and Timezone)
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_settings = load_settings().get(username, {'language': 'en', 'timezone': 'UTC'})

    if request.method == 'POST':
        language = request.form['language']
        timezone = request.form['timezone']

        settings = {'language': language, 'timezone': timezone}
        save_settings(username, settings)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', user_settings=user_settings, timezone_choices=TIMEZONE_CHOICES)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
