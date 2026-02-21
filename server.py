"""
Example Flask app — a simple task management API.
Contains intentional bugs for testing the BugPilot pipeline.
"""

from flask import Flask, jsonify, request
from .database import db, Task
from .auth import require_auth, create_token

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db.init_app(app)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ── Auth ─────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = db.execute(
        f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    ).fetchone()

    if user:
        token = create_token(user["id"], user["username"])
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401


# ── Tasks CRUD ───────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
@require_auth
def list_tasks():
    """List all tasks for the authenticated user."""
    user_id = request.user_id
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route("/api/tasks", methods=["POST"])
@require_auth
def create_task():
    """Create a new task."""
    data = request.get_json()
    title = data.get("title")

    if not title:
        return jsonify({"error": "Title is required"}), 400

    task = Task(
        title=title,
        description=data.get("description", ""),
        user_id=request.user_id,
        # BUG: status field not set — defaults to None instead of "pending"
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@require_auth
def update_task(task_id):
    """Update a task."""
    task = Task.query.get(task_id)

    # BUG: Missing authorization check — any user can update any task
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)
    db.session.commit()
    return jsonify(task.to_dict())


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@require_auth
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get(task_id)

    # BUG: No ownership check — any authenticated user can delete any task
    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"deleted": True})


@app.route("/api/tasks/search", methods=["GET"])
@require_auth
def search_tasks():
    """Search tasks by title."""
    query = request.args.get("q", "")

    # BUG: SQL injection — user input directly interpolated
    results = db.execute(
        f"SELECT * FROM tasks WHERE title LIKE '%{query}%' AND user_id={request.user_id}"
    ).fetchall()

    return jsonify([dict(r) for r in results])

