from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from functools import wraps
from datetime import timedelta
from flask_mail import Mail, Message
import secrets

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.permanent_session_lifetime = timedelta(minutes=30)

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Database configuration
db_config = {
    "host": os.environ.get('DB_HOST', "localhost"),
    "user": os.environ.get('DB_USER', "root"),
    "password": os.environ.get('DB_PASSWORD', "root"),
    "database": os.environ.get('DB_NAME', "quiz_db"),
    "raise_on_warnings": True
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Database connection failed: {str(e)}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "alert-danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def validate_input(data):
    return data.strip() if data and isinstance(data, str) else None

def generate_reset_token():
    return secrets.token_urlsafe(32)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("quiz"))

    if request.method == "POST":
        username = validate_input(request.form.get("username"))
        password = validate_input(request.form.get("password"))

        if not username or not password:
            flash("Please fill in all fields.", "alert-danger")
            return render_template("login.html")
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "alert-danger")
            return render_template("login.html")

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user["password"], password):
                session.permanent = True
                session["user_id"] = user["user_id"]
                flash("Login successful!", "alert-success")
                return redirect(url_for("quiz"))
            else:
                flash("Invalid username or password", "alert-danger")
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            if cursor:
                cursor.close()
            conn.close()

    return render_template("login.html")

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "alert-danger")
        return redirect(url_for("login"))

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        
        if not questions:
            flash("No questions available.", "alert-danger")
            return redirect(url_for("index"))

        if request.method == "POST":
            answer_id = request.form.get("answer")
            question_id = request.form.get("question_id")
            cursor.execute("SELECT is_correct FROM answers WHERE answer_id = %s", (answer_id,))
            answer = cursor.fetchone()
            if answer:
                session["score"] = session.get("score", 0) + (1 if answer["is_correct"] else 0)
            session["question_index"] = session.get("question_index", 0) + 1
            
            if session["question_index"] >= len(questions):
                score = session.pop("score", 0)
                total = len(questions)
                session.pop("question_index", None)
                return render_template("results.html", score=score, total=total)
        
        question_index = session.get("question_index", 0)
        if question_index >= len(questions):
            session.pop("question_index", None)
            session.pop("score", None)
            question_index = 0
        
        cursor.execute("SELECT * FROM answers WHERE question_id = %s", (questions[question_index]["question_id"],))
        answers = cursor.fetchall()
        return render_template("question.html", question=questions[question_index], answers=answers, 
                              question_index=question_index, questions=questions)
    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = validate_input(request.form.get("username"))
        email = validate_input(request.form.get("email"))
        password = validate_input(request.form.get("password"))

        if not username or not email or not password:
            flash("Please fill in all fields.", "alert-danger")
            return render_template("register.html")
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "alert-danger")
            return render_template("register.html")

        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "alert-danger")
                return render_template("register.html")
            
            cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already in use.", "alert-danger")
                return render_template("register.html")
            
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                          (username, email, hashed_password))
            conn.commit()
            flash("Registration successful! Please log in.", "alert-success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            if cursor:
                cursor.close()
            conn.close()

    return render_template("register.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = validate_input(request.form.get("email"))
        if not email:
            flash("Please enter an email address.", "alert-danger")
            return render_template("reset_password.html")
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "alert-danger")
            return render_template("reset_password.html")

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                token = generate_reset_token()
                cursor.execute("UPDATE users SET reset_token = %s WHERE user_id = %s", (token, user["user_id"]))
                conn.commit()
                
                reset_link = url_for("reset_password_confirm", token=token, _external=True)
                msg = Message("Password Reset Request", 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[email])
                msg.body = f"Hi {user['username']},\n\nTo reset your password, click the following link:\n{reset_link}\n\nIf you didn’t request this, please ignore this email."
                mail.send(msg)
            flash("If an account exists with that email, a reset link has been sent.", "alert-success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            if cursor:
                cursor.close()
            conn.close()
    return render_template("reset_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password_confirm(token):
    if request.method == "POST":
        password = validate_input(request.form.get("password"))
        if not password:
            flash("Please enter a new password.", "alert-danger")
            return render_template("reset_password_confirm.html", token=token)
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "alert-danger")
            return render_template("reset_password_confirm.html", token=token)

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM users WHERE reset_token = %s", (token,))
            user = cursor.fetchone()
            if not user:
                flash("Invalid or expired reset link.", "alert-danger")
                return redirect(url_for("reset_password"))
            
            hashed_password = generate_password_hash(password)
            cursor.execute("UPDATE users SET password = %s, reset_token = NULL WHERE user_id = %s", 
                          (hashed_password, user["user_id"]))
            conn.commit()
            flash("Password reset successful! Please log in.", "alert-success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            if cursor:
                cursor.close()
            conn.close()
    return render_template("reset_password_confirm.html", token=token)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "alert-success")
    return redirect(url_for("index"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')