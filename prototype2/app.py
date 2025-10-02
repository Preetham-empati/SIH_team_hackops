from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from functools import wraps
import json
import os
import uuid
import calendar
from pathway_service import get_user_pathway, save_user_pathway, generate_new_pathway

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_change_me'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'profile_pics')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- Flask-Mail Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'hackops2025@gmail.com'
app.config['MAIL_PASSWORD'] = 'dxwgqecnbkvtwyks'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Custom Template Filter ---
@app.template_filter('month_name')
def month_name_filter(month_number):
    try:
        # calendar.month_abbr is a list where index 1 is 'Jan', etc.
        return calendar.month_abbr[int(month_number)]
    except (IndexError, ValueError):
        return ''

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not password or not email:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password, is_verified, profile_complete, profile_picture) VALUES (?, ?, ?, ?, ?, ?)',
                (username, email, hashed_password, False, False, 'default_profile.png')
            )
            conn.commit()

            otp = ''.join(random.choices(string.digits, k=6))
            session['otp'] = otp
            session['otp_email'] = email

            msg = Message('Your Verification Code for SkillSync AI', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your one-time verification code is: {otp}'
            mail.send(msg)
            
            flash('Registration successful! An OTP has been sent to your email.', 'info')
            return redirect(url_for('verify_otp'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp_email' not in session:
        return redirect(url_for('register'))

    if request.method == 'POST':
        submitted_otp = request.form['otp']
        
        if 'otp' in session and session['otp'] == submitted_otp:
            email_to_verify = session['otp_email']
            conn = get_db_connection()
            conn.execute('UPDATE users SET is_verified = ? WHERE email = ?', (True, email_to_verify))
            conn.commit()
            conn.close()
            session.pop('otp', None)
            flash('Email verified successfully! Please complete your profile.', 'success')
            return redirect(url_for('create_profile'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if 'otp_email' not in session:
        flash('Please verify your email first.', 'warning')
        return redirect(url_for('register'))

    if request.method == 'POST':
        email = session['otp_email']
        gender = request.form['gender']
        study_age = request.form['study_age']
        interests = request.form['interests']
        aspirations = request.form['aspirations']
        achievements = request.form['achievements']
        
        profile_picture_filename = 'default_profile.png'
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_picture_filename = filename
            elif file.filename != '':
                flash('Allowed image types are png, jpg, jpeg, gif', 'danger')
                return redirect(url_for('create_profile'))

        conn = get_db_connection()
        conn.execute('''
            UPDATE users SET gender=?, study_age=?, interests=?, aspirations=?, achievements=?, profile_complete=?, profile_picture=?
            WHERE email=?
        ''', (gender, study_age, interests, aspirations, achievements, True, profile_picture_filename, email))
        conn.commit()
        conn.close()
        
        session.pop('otp_email', None)
        flash('Profile created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('create_profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            if not user['is_verified']:
                flash('Your account is not verified. Please register again.', 'warning')
                return redirect(url_for('login'))
            
            if not user['profile_complete']:
                session['otp_email'] = user['email']
                flash('Please complete your profile before logging in.', 'warning')
                return redirect(url_for('create_profile'))

            session['username'] = user['username']
            session['profile_picture'] = user['profile_picture'] if user['profile_picture'] else 'default_profile.png'
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()

    if request.method == 'POST':
        gender = request.form['gender']
        study_age = request.form['study_age']
        interests = request.form['interests']
        aspirations = request.form['aspirations']
        achievements = request.form['achievements']
        profile_picture_filename = user['profile_picture']

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                if profile_picture_filename and profile_picture_filename != 'default_profile.png':
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], profile_picture_filename)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_picture_filename = filename
                session['profile_picture'] = profile_picture_filename
            elif file.filename != '':
                flash('Allowed image types are png, jpg, jpeg, gif', 'danger')
                return redirect(url_for('profile'))
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE users SET gender=?, study_age=?, interests=?, aspirations=?, achievements=?, profile_picture=?
            WHERE username=?
        ''', (gender, study_age, interests, aspirations, achievements, profile_picture_filename, session['username']))
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()
    
    pathway_data = get_user_pathway(user['id'])

    if not pathway_data:
        return redirect(url_for('generate_pathway_form'))

    completed_courses, in_progress_courses, upcoming_courses, overall_progress = 0, 0, 0, 0
    if pathway_data and 'steps' in pathway_data:
        completed_courses = sum(1 for step in pathway_data['steps'] if step.get('status') == 'completed')
        in_progress_courses = sum(1 for step in pathway_data['steps'] if step.get('status') == 'in_progress')
        upcoming_courses = sum(1 for step in pathway_data['steps'] if step.get('status') == 'not_started')
        total_courses = len(pathway_data['steps'])
        overall_progress = int((completed_courses / total_courses) * 100) if total_courses > 0 else 0

    learning_activity = {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "data": [10, 15, 12, 20, 25, 22]}
    upcoming_schedule = [{"date": "2025-10-05", "title": "Webinar: Intro to React Hooks", "time": "4:00 PM"}, {"date": "2025-10-12", "title": "Project Submission: JS Basics", "time": "11:59 PM"}]
    popular_courses = [{"title": "UI/UX Design Fundamentals", "students": "1200+", "image": "https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?w=500"}, {"title": "Data Science with Python", "students": "2500+", "image": "https://images.unsplash.com/photo-1555255707-c07969078f46?w=500"}]
    notifications = [{"type": "reminder", "content": "Your 'JavaScript Basics' project is due soon.", "time": "1h ago"}, {"type": "badge", "content": "Congratulations! You've earned the 'HTML5 Expert' badge.", "time": "3d ago"}]

    return render_template('dashboard.html', pathway=pathway_data, completed=completed_courses, in_progress=in_progress_courses, upcoming=upcoming_courses, progress=overall_progress, activity=learning_activity, schedule=upcoming_schedule, popular=popular_courses, notifications=notifications)

@app.route('/generate_pathway', methods=['GET', 'POST'])
@login_required
def generate_pathway_form():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()

    if request.method == 'POST':
        aspiration = request.form['aspiration']
        if not aspiration:
            flash('Please enter your career aspiration.', 'danger')
            return redirect(url_for('generate_pathway_form'))

        new_pathway = generate_new_pathway(user, aspiration)

        if new_pathway:
            save_user_pathway(user['id'], new_pathway)
            flash('Your personalized pathway has been successfully generated!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('There was an error generating your pathway. Please try again.', 'danger')
            return redirect(url_for('generate_pathway_form'))

    return render_template('generate_pathway.html', user=user)

@app.route('/my_courses')
@login_required
def my_courses():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()
    
    pathway_data = get_user_pathway(user['id'])

    return render_template('my_courses.html', pathway=pathway_data)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('profile_picture', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

