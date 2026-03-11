from flask import Flask, render_template, request
from services.question_api import fetch_questions
from templates.geminiquizgenerate import fetch_questions_gemini

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        # This handles the data when the user clicks the "Generate" button
        subject = request.form.get("subject")
        mastered = request.form.get("mastered")
        focus = request.form.get("focus")
    else:
        # This handles when someone just types the URL in directly
        subject = request.args.get("subject")
        mastered = request.args.get("mastered")
        focus = request.args.get("focus")

    #calling Gemini function
    questions = fetch_questions_gemini(
        subject=subject,
        mastered=mastered,
        focus=focus
    )

    return render_template(
        "geminiquizquestion.html",
        questions=questions,
        subject=subject,
        focus=focus
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
