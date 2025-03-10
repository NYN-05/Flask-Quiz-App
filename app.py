from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
from functools import wraps
from datetime import timedelta

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.permanent_session_lifetime = timedelta(minutes=30)

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

@app.route("/", methods=["GET", "POST"])
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
            cursor.close()
            conn.close()

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = validate_input(request.form.get("username"))
        password = validate_input(request.form.get("password"))

        if not username or not password:
            flash("Please fill in all fields.", "alert-danger")
            return render_template("register.html")
        
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "alert-danger")
            return render_template("register.html")

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please log in.", "alert-success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
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
        flash("If an account exists, a reset link has been sent.", "alert-success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "alert-success")
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
