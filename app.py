from flask import Flask, render_template, request
from services.question_api import fetch_questions


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/trialform")
def form():
    return render_template("trialform.html")

@app.route("/quiz")
def quiz():
    subject = request.args.get("subject")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")

    questions = fetch_questions(
        amount=5,
        category=category,
        difficulty=difficulty
    )

    return render_template(
        "quiz.html",
        questions=questions,
        subject=subject,
        difficulty=difficulty
    )



@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    score = 0
    total = 5

    for i in range(1, total + 1):
        if request.form.get(f"q{i}") == request.form.get(f"correct{i}"):
            score += 1

    subject = request.form.get("subject")
    difficulty = request.form.get("difficulty")

    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO performance (subject, difficulty, score, total)
        VALUES (?, ?, ?, ?)
        """,
        (subject, difficulty, score, total)
    )

    conn.commit()
    conn.close()

    return render_template("result.html", score=score, total=total)

@app.route("/dashboard")
def dashboard():
    import sqlite3

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject, difficulty, score, total
        FROM performance
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", records=records)

if __name__ == "__main__":
    app.run(debug=True)
