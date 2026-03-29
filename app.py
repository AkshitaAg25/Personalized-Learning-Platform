import sqlite3, os, json, functools
from flask import Flask, render_template, request, session, redirect, url_for, flash
from templates.geminiquizgenerate import fetch_questions_gemini
from utils.evaluation import evaluate_quiz
from utils.knowledge_graph import build_knowledge_graph
from utils.recommendation import build_recommendation_path
from utils.auth import register_user, login_user, get_user_by_id

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mindmap-dev-secret-2025")
DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def current_user():
    uid = session.get("user_id")
    return get_user_by_id(uid) if uid else None

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET","POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        ok, msg = register_user(
            request.form.get("username",""),
            request.form.get("email",""),
            request.form.get("password","")
        )
        if ok:
            flash(msg, "success")
            return redirect(url_for("login"))
        flash(msg, "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user, msg = login_user(
            request.form.get("username_or_email",""),
            request.form.get("password","")
        )
        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        flash(msg, "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))

# ── Public pages ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", user=current_user())

@app.route("/form")
@login_required
def form():
    return render_template("form.html", user=current_user())

# ── Quiz ──────────────────────────────────────────────────────────────────────

@app.route("/quiz", methods=["GET","POST"])
@login_required
def quiz():
    if request.method == "POST":
        subject  = request.form.get("subject")
        mastered = request.form.get("mastered")
        focus    = request.form.get("focus")
    else:
        subject  = request.args.get("subject")
        mastered = request.args.get("mastered")
        focus    = request.args.get("focus")

    questions = fetch_questions_gemini(subject=subject, mastered=mastered, focus=focus)
    return render_template("geminiquizquestion.html",
        questions=questions, subject=subject, focus=focus, mastered=mastered, user=current_user())

@app.route("/submit-quiz", methods=["POST"])
@login_required
def submit_quiz():
    user_id = session["user_id"]

    eval_result = evaluate_quiz(request.form)
    kg          = build_knowledge_graph(eval_result)
    rec         = build_recommendation_path(eval_result, kg)

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO performance (user_id,subject,focus,mastered,difficulty,score,total,percentage,level,timestamp)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (user_id, eval_result["subject"], eval_result["focus"], eval_result["mastered"],
          eval_result["level"], eval_result["score"], eval_result["total"],
          eval_result["percentage"], eval_result["level"], eval_result["timestamp"]))
    perf_id = cur.lastrowid

    for topic, data in eval_result["topic_scores"].items():
        cur.execute(
            "INSERT INTO topic_scores (performance_id,topic,correct,total,accuracy) VALUES (?,?,?,?,?)",
            (perf_id, topic, data["correct"], data["total"], data["accuracy"]))

    # Upsert knowledge snapshot for this subject
    cur.execute("""
        INSERT INTO knowledge_snapshots (user_id,subject,nodes_json,edges_json,updated_at)
        VALUES (?,?,?,?,datetime('now'))
        ON CONFLICT(user_id,subject) DO UPDATE SET
            nodes_json=excluded.nodes_json,
            edges_json=excluded.edges_json,
            updated_at=datetime('now')
    """, (user_id, eval_result["subject"], json.dumps(kg["nodes"]), json.dumps(kg["edges"])))

    conn.commit(); conn.close()

    session["eval_result"]    = eval_result
    session["knowledge_graph"]= kg
    session["recommendation"] = rec

    return render_template("result.html",
        eval_result=eval_result, recommendation=rec,
        graph_nodes_json=json.dumps(kg["nodes"]),
        graph_edges_json=json.dumps(kg["edges"]),
        user=current_user())

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn    = get_db()
    cur     = conn.cursor()

    # Full history for this user
    cur.execute("""
        SELECT id,subject,focus,level,score,total,percentage,timestamp
        FROM performance WHERE user_id=? ORDER BY id DESC
    """, (user_id,))
    records = cur.fetchall()

    # Per-subject aggregates
    cur.execute("""
        SELECT subject, ROUND(AVG(percentage),1) as avg_pct, COUNT(*) as attempts,
               MAX(percentage) as best_pct,
               SUM(CASE WHEN level='advanced' THEN 1 ELSE 0 END) as adv_count
        FROM performance WHERE user_id=? GROUP BY subject ORDER BY attempts DESC
    """, (user_id,))
    subject_stats = cur.fetchall()

    # Global topic accuracy for this user
    cur.execute("""
        SELECT ts.topic, ROUND(AVG(ts.accuracy),1) as avg_acc,
               SUM(ts.correct) as total_correct, SUM(ts.total) as total_q
        FROM topic_scores ts
        JOIN performance p ON ts.performance_id=p.id
        WHERE p.user_id=? GROUP BY ts.topic ORDER BY avg_acc ASC
    """, (user_id,))
    topic_stats = cur.fetchall()

    # Knowledge snapshots (latest graph per subject)
    cur.execute("""
        SELECT subject,nodes_json,edges_json,updated_at
        FROM knowledge_snapshots WHERE user_id=? ORDER BY updated_at DESC
    """, (user_id,))
    snapshots = cur.fetchall()

    conn.close()

    return render_template("dashboard.html",
        records=records, subject_stats=subject_stats,
        topic_stats=topic_stats, snapshots=snapshots, user=current_user())

# ── Recommendation standalone page ───────────────────────────────────────────

@app.route("/recommendation")
@login_required
def recommendation():
    rec         = session.get("recommendation", {})
    eval_result = session.get("eval_result", {})
    kg          = session.get("knowledge_graph", {})
    return render_template("recommendation.html",
        recommendation=rec, eval_result=eval_result,
        graph_nodes_json=json.dumps(kg.get("nodes",[])),
        graph_edges_json=json.dumps(kg.get("edges",[])),
        user=current_user())

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        import utils.init_db
    app.run(debug=True)
