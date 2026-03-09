# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Intentionally Buggy Flask Application for ARRIVAL Phase 18
==========================================================
This application contains exactly 10 intentional bugs/vulnerabilities
for the security audit experiment. Each bug is a distinct class of error.

DO NOT FIX — this is the test artifact. See bugs_ground_truth.json for details.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

import sqlite3
import hashlib
import logging
import os
import json
import threading
from datetime import datetime

from flask import Flask, request, jsonify, session, redirect, render_template_string

app = Flask(__name__)
app.secret_key = "super_secret_key_12345"  # BUG 7: Hardcoded secret in source

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DB_PATH = "app_data.db"
UPLOAD_DIR = "uploads"

# Global counter for rate limiting (shared mutable state)
request_counter = {"count": 0, "window_start": datetime.now()}


def init_db():
    """Initialize SQLite database with users and notes tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user',
        balance REAL DEFAULT 0.0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        created_at TEXT,
        is_private INTEGER DEFAULT 1
    )""")
    conn.commit()
    conn.close()


init_db()


# ============================================================
# BUG 1: SQL Injection in login
# ============================================================
@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and create session."""
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # BUG 1: Direct string interpolation → SQL injection
    query = f"SELECT id, role FROM users WHERE username='{username}' AND password_hash='{hashlib.md5(password.encode()).hexdigest()}'"
    c.execute(query)
    user = c.fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["role"] = user[1]
        logger.info(f"Login successful: user={username}, password={password}")  # BUG 7b: Logging password
        return jsonify({"status": "ok", "user_id": user[0]})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


# ============================================================
# BUG 2: Missing authorization check (IDOR)
# ============================================================
@app.route("/users/<int:user_id>/notes", methods=["GET"])
def get_user_notes(user_id):
    """Get all notes for a user. BUG: No auth check — any user can read any user's notes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, content, created_at FROM notes WHERE user_id=?", (user_id,))
    notes = [{"id": r[0], "title": r[1], "content": r[2], "created_at": r[3]} for r in c.fetchall()]
    conn.close()
    return jsonify(notes)


# ============================================================
# BUG 3: Race condition in balance transfer
# ============================================================
@app.route("/transfer", methods=["POST"])
def transfer_balance():
    """Transfer balance between users. BUG: No atomic transaction → race condition."""
    data = request.get_json()
    from_id = data.get("from_user_id")
    to_id = data.get("to_user_id")
    amount = float(data.get("amount", 0))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # BUG 3: Read-then-write without transaction lock → TOCTOU race condition
    c.execute("SELECT balance FROM users WHERE id=?", (from_id,))
    sender = c.fetchone()
    if not sender or sender[0] < amount:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    # Another thread could read the same balance here before we update
    c.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, from_id))
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, to_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "transferred", "amount": amount})


# ============================================================
# BUG 4: Off-by-one error in pagination
# ============================================================
@app.route("/notes", methods=["GET"])
def list_notes():
    """List notes with pagination. BUG: Off-by-one causes first note to be skipped."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    # BUG 4: offset starts at 1 instead of 0 → first item always skipped
    offset = page * per_page + 1

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, content FROM notes LIMIT ? OFFSET ?", (per_page, offset))
    notes = [{"id": r[0], "title": r[1], "content": r[2]} for r in c.fetchall()]
    conn.close()

    return jsonify({"page": page, "per_page": per_page, "notes": notes})


# ============================================================
# BUG 5: Incorrect sorting algorithm (wrong comparison)
# ============================================================
@app.route("/notes/sorted", methods=["GET"])
def sorted_notes():
    """Return notes sorted by creation date. BUG: Comparison is inverted."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, content, created_at FROM notes")
    notes = [{"id": r[0], "title": r[1], "content": r[2], "created_at": r[3]} for r in c.fetchall()]
    conn.close()

    sort_order = request.args.get("order", "asc")

    # BUG 5: Comparison operators are swapped — "asc" actually sorts descending
    if sort_order == "asc":
        notes.sort(key=lambda n: n["created_at"] or "", reverse=True)   # Wrong! reverse=True is DESC
    else:
        notes.sort(key=lambda n: n["created_at"] or "", reverse=False)  # Wrong! reverse=False is ASC

    return jsonify(notes)


# ============================================================
# BUG 6: XSS vulnerability (unescaped user input in HTML)
# ============================================================
@app.route("/note/<int:note_id>/view")
def view_note(note_id):
    """Render a note as HTML. BUG: User content injected without escaping → XSS."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, content FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()

    if not note:
        return "Note not found", 404

    # BUG 6: Direct injection of user content into HTML without escaping
    html = f"""
    <html>
    <head><title>{note[0]}</title></head>
    <body>
        <h1>{note[0]}</h1>
        <div class="content">{note[1]}</div>
    </body>
    </html>
    """
    return html


# ============================================================
# BUG 7: Secret/credential leak in logs (see also line 25: hardcoded secret)
# ============================================================
@app.route("/register", methods=["POST"])
def register():
    """Register a new user. BUG: Password logged in plaintext (see login too)."""
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")
    email = data.get("email", "")

    # BUG 7: Logging sensitive data (password in plaintext)
    logger.debug(f"Registration attempt: user={username}, pass={password}, email={email}")

    password_hash = hashlib.md5(password.encode()).hexdigest()  # Also: MD5 is weak, but that's BUG 10

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                  (username, password_hash, email))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 409
    conn.close()

    return jsonify({"status": "registered", "user_id": user_id}), 201


# ============================================================
# BUG 8: Incorrect Unicode handling (mojibake / data corruption)
# ============================================================
@app.route("/notes", methods=["POST"])
def create_note():
    """Create a new note. BUG: Unicode content is corrupted by encoding chain."""
    data = request.get_json()
    user_id = data.get("user_id")
    title = data.get("title", "")
    content = data.get("content", "")

    # BUG 8: Encode as UTF-8 then decode as latin-1 → corrupts non-ASCII characters
    processed_content = content.encode("utf-8").decode("latin-1")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
              (user_id, title, processed_content, datetime.now().isoformat()))
    conn.commit()
    note_id = c.lastrowid
    conn.close()

    return jsonify({"status": "created", "note_id": note_id}), 201


# ============================================================
# BUG 9: Integer overflow in calculation
# ============================================================
@app.route("/calculate-discount", methods=["POST"])
def calculate_discount():
    """Calculate discount for bulk orders. BUG: Integer overflow with large quantities."""
    data = request.get_json()
    quantity = int(data.get("quantity", 0))
    unit_price_cents = int(data.get("unit_price_cents", 0))

    # BUG 9: Multiplication can overflow for large values.
    # Python handles big ints natively, but the real bug is:
    # the discount calculation wraps around due to modular arithmetic
    # applied intentionally to simulate fixed-width int behavior
    total_cents = (quantity * unit_price_cents) & 0xFFFFFFFF  # 32-bit truncation

    # Apply discount tiers
    if total_cents > 100000:  # > $1000
        discount = 0.15
    elif total_cents > 50000:  # > $500
        discount = 0.10
    elif total_cents > 10000:  # > $100
        discount = 0.05
    else:
        discount = 0.0

    final_cents = int(total_cents * (1 - discount))
    return jsonify({
        "quantity": quantity,
        "unit_price_cents": unit_price_cents,
        "total_cents": total_cents,
        "discount_percent": discount * 100,
        "final_cents": final_cents,
    })


# ============================================================
# BUG 10: Weak error handling (bare except, swallowed errors)
# ============================================================
@app.route("/import-notes", methods=["POST"])
def import_notes():
    """Import notes from JSON upload. BUG: Bare except swallows all errors silently."""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400

        raw = file.read()
        notes_data = json.loads(raw)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        imported = 0
        for note in notes_data:
            try:
                # BUG 10: Bare except catches EVERYTHING (KeyboardInterrupt, SystemExit, etc.)
                # and silently continues — data corruption goes unnoticed
                c.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
                          (note["user_id"], note["title"], note["content"], datetime.now().isoformat()))
                imported += 1
            except:  # noqa: E722 — bare except is the bug
                pass  # Silently swallow ALL errors including malformed data

        conn.commit()
        conn.close()
        return jsonify({"status": "imported", "count": imported})

    except:  # noqa: E722 — another bare except
        return jsonify({"status": "ok", "count": 0})  # Hides the real error, returns misleading "ok"


# ============================================================
# Additional helper routes
# ============================================================
@app.route("/health")
def health():
    return jsonify({"status": "healthy", "db": DB_PATH})


@app.route("/admin/users", methods=["GET"])
def admin_list_users():
    """Admin endpoint. BUG 2b: No role check — accessible to everyone."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, email, role, balance FROM users")
    users = [{"id": r[0], "username": r[1], "email": r[2], "role": r[3], "balance": r[4]}
             for r in c.fetchall()]
    conn.close()
    return jsonify(users)


if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)  # debug=True in production is also bad
