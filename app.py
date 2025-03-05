from flask import Flask, render_template, request, redirect, url_for, session, flash
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
        return mysql.connector.connect(**db_config)
    except Error as e:
        flash(f"Database connection failed: {str(e)}", "alert-danger")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "alert-danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("quiz"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        print(f"Login attempt - Username: {username}")  # Debug
        
        if not username or not password:
            flash("Please fill in all fields.", "alert-danger")
            return render_template("login.html")
            
        conn = get_db_connection()
        if not conn:
            print("Database connection failed")  # Debug
            return render_template("login.html")
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            print(f"User found: {user is not None}")  # Debug
            print(f"Stored hash: {user['password'] if user else 'None'}")  # Debug
            
            if user and check_password_hash(user["password"], password):
                session.permanent = True
                session["user_id"] = user["user_id"]
                flash("Login successful!", "alert-success")
                return redirect(url_for("quiz"))
            else:
                flash("Invalid username or password", "alert-danger")
        except Error as e:
            print(f"Database error: {str(e)}")  # Debug
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            cursor.close()
            conn.close()
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please fill in all fields.", "alert-danger")
            return render_template("register.html")
            
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "alert-danger")
            return render_template("register.html")
            
        conn = get_db_connection()
        if not conn:
            return render_template("register.html")
            
        try:
            cursor = conn.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                         (username, hashed_password))
            conn.commit()
            flash("Registration successful! Please login.", "alert-success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Username already exists", "alert-danger")
        except Error as e:
            flash(f"Error: {str(e)}", "alert-danger")
        finally:
            cursor.close()
            conn.close()
            
    return render_template("register.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please enter an email address.", "alert-danger")
            return render_template("reset_password.html")
        flash("If an account exists, a reset link has been sent.", "alert-success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.route("/quiz")
@login_required
def quiz():
    conn = get_db_connection()
    if not conn:
        return redirect(url_for("login"))
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 5")
        questions = cursor.fetchall()
        
        if not questions:
            flash("No questions available.", "alert-danger")
            return redirect(url_for("login"))
            
        session["questions"] = [dict(q) for q in questions]
        session["score"] = 0
        session["question_index"] = 0
        return redirect(url_for("question"))
    finally:
        cursor.close()
        conn.close()

@app.route("/question", methods=["GET", "POST"])
@login_required
def question():
    questions = session.get("questions")
    if not questions:
        return redirect(url_for("login"))
        
    question_index = session.get("question_index", 0)
    if question_index >= len(questions):
        return redirect(url_for("results"))
        
    question = questions[question_index]
    
    conn = get_db_connection()
    if not conn:
        return redirect(url_for("login"))
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM answers WHERE question_id = %s", (question["question_id"],))
        answers = cursor.fetchall()
        
        if request.method == "POST":
            try:
                user_answer = int(request.form.get("answer", 0))
                correct_answer_id = next((a["answer_id"] for a in answers if a["is_correct"]), None)
                
                is_correct = user_answer == correct_answer_id
                session["score"] = session.get("score", 0) + (1 if is_correct else 0)
                
                cursor.execute("INSERT INTO scores (user_id, question_id, is_correct) VALUES (%s, %s, %s)",
                             (session["user_id"], question["question_id"], is_correct))
                conn.commit()
                
                session["question_index"] = question_index + 1
                flash("Correct!" if is_correct else "Incorrect.", 
                      "alert-success" if is_correct else "alert-danger")
                return redirect(url_for("question"))
            except ValueError:
                flash("Please select an answer.", "alert-danger")
                
        return render_template("question.html", 
                            question=question, 
                            answers=answers, 
                            question_index=question_index)
    finally:
        cursor.close()
        conn.close()

@app.route("/results")
@login_required
def results():
    score = session.get("score", 0)
    total = len(session.get("questions", []))
    session.pop("questions", None)
    session.pop("question_index", None)
    return render_template("results.html", score=score, total=total)

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