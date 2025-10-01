from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'

## (in app.py)

# --- Flask-Mail Configuration ---
# This part remains the same. You still need your App Password.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'hackops2025@gmail.com' # Make sure this is your correct email

# REPLACE the placeholder with your new App Password
app.config['MAIL_PASSWORD'] = 'dxwgqecnbkvtwyks' 

app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# ... the rest of your app.py code ...

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

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
                'INSERT INTO users (username, email, password, is_verified) VALUES (?, ?, ?, ?)',
                (username, email, hashed_password, False)
            )
            conn.commit()

            # --- NEW: Generate and Send OTP ---
            otp = ''.join(random.choices(string.digits, k=6))
            session['otp'] = otp
            session['otp_email'] = email # Store email to verify later

            msg = Message('Your Verification Code for SkillSync AI', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your one-time verification code is: {otp}'
            mail.send(msg)
            # -----------------------------------

            flash('Registration successful! An OTP has been sent to your email.', 'info')
            return redirect(url_for('verify_otp')) # Redirect to the new OTP page

        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

# --- NEW ROUTE for OTP Verification ---
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp_email' not in session:
        flash('Invalid request. Please register first.', 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        submitted_otp = request.form['otp']
        
        if 'otp' in session and session['otp'] == submitted_otp:
            email_to_verify = session['otp_email']

            conn = get_db_connection()
            conn.execute('UPDATE users SET is_verified = ? WHERE email = ?', (True, email_to_verify))
            conn.commit()
            conn.close()
            
            # Clear session variables
            session.pop('otp', None)
            session.pop('otp_email', None)

            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


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
                flash('Your account is not verified. Please register again to receive a new OTP.', 'warning')
                return redirect(url_for('login'))
            
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)