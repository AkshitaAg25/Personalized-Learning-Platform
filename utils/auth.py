
import hashlib, os, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")

def _hash(password: str) -> str:
    salt = "mindmap_salt_v1"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username.strip(), email.strip().lower(), _hash(password))
        )
        conn.commit()
        conn.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError as e:
        msg = "Username already taken." if "username" in str(e) else "Email already registered."
        return False, msg

def login_user(username_or_email: str, password: str) -> tuple[dict | None, str]:
    conn = get_db()
    val  = username_or_email.strip().lower()
    row  = conn.execute(
        "SELECT * FROM users WHERE LOWER(username)=? OR LOWER(email)=?", (val, val)
    ).fetchone()
    conn.close()
    if not row:
        return None, "No account found with that username or email."
    if row["password_hash"] != _hash(password):
        return None, "Incorrect password."
    return dict(row), "Logged in."

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
