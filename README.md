# Flask-Quiz-App

A modern, responsive quiz application built with Flask, MySQL, and a sleek front-end design. This project allows users to register, log in, take quizzes, and view their results, all while featuring a professional UI with animations and gradient styling.

## Table of Contents

- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **User Authentication:** Secure registration and login with password hashing.
- **Quiz System:** Randomized questions with multiple-choice answers and real-time scoring.
- **Responsive Design:** Mobile-friendly UI with modern styling (gradients, shadows, animations).
- **Results Tracking:** Displays scores and percentages after quiz completion.
- **Error Handling:** Robust handling of database errors and user input validation.
- **Session Management:** Persistent user sessions with a 30-minute timeout.

## Technologies

- **Backend:** Flask (Python web framework)
- **Database:** MySQL (for storing users, questions, answers, and scores)
- **Frontend:** HTML, CSS (with Poppins font via Google Fonts)
- **Security:** Werkzeug for password hashing
- **Dependencies:** mysql-connector-python, flask, werkzeug

## Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Git

### Steps

#### Clone the Repository

```bash
git clone https://github.com/your-username/Flask-Quiz-App.git
cd Flask-Quiz-App
```

#### Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure MySQL

Create a database named `quiz_db`:

```sql
CREATE DATABASE quiz_db;
```

Update the database configuration in `app.py` if necessary:

```python
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "quiz_db"
}
```

#### Set Up the Database Schema

Run the following SQL commands in your MySQL client:

```sql
USE quiz_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL
);

CREATE TABLE answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

CREATE TABLE scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    question_id INT,
    is_correct BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

-- Sample data
INSERT INTO users (username, password) VALUES
    ('testuser', '$2b$12$YOUR_HASH_HERE'); -- Generate with generate_password_hash('testpass')

INSERT INTO questions (question_text) VALUES
    ('What is 2 + 2?'),
    ('What is the capital of France?');

INSERT INTO answers (question_id, answer_text, is_correct) VALUES
    (1, '3', FALSE),
    (1, '4', TRUE),
    (1, '5', FALSE),
    (2, 'Paris', TRUE),
    (2, 'London', FALSE),
    (2, 'Berlin', FALSE);
```

#### Run the Application

```bash
python app.py
```

Access the app at `http://localhost:5000`.

## Usage

- **Register:** Create an account with a username and password (min. 8 characters).
- **Login:** Use your credentials to log in.
- **Take a Quiz:** Start a quiz with 5 random questions.
- **View Results:** See your score and percentage after completion.
- **Logout:** End your session securely.

## Project Structure

```
Flask-Quiz-App/
├── static/
│   └── styles.css          # Enhanced CSS with modern styling
├── templates/
│   ├── base.html          # Base template with navigation
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── reset_password.html# Password reset page
│   ├── question.html      # Quiz question page
│   ├── results.html       # Results page
│   └── 404.html           # 404 error page
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Database Schema

| Table         | Columns                                                                  |
| ------------- | ------------------------------------------------------------------------ |
| **users**     | user\_id (PK), username (UNIQUE), password                               |
| **questions** | question\_id (PK), question\_text                                        |
| **answers**   | answer\_id (PK), question\_id (FK), answer\_text, is\_correct            |
| **scores**    | score\_id (PK), user\_id (FK), question\_id (FK), is\_correct, timestamp |

## Screenshots

(Add screenshots here after deploying or testing locally)

- **Login Page:** ![Insert image URL or path]
- **Quiz Page:** ![Insert image URL or path]
- **Results Page:** ![Insert image URL or path]

## Contributing

Contributions are welcome! Follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit (`git commit -m "Add your feature"`).
4. Push to your branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please ensure your code follows PEP 8 guidelines and includes appropriate comments.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or suggestions, feel free to reach out:

- **GitHub:** [https://github.com/NYN-05](https://github.com/NYN-05)
- **Email:** [jnyn2005@.com](mailto\:jnyn2005@gmail.com)

