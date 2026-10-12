from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import date

app = Flask(__name__)
app.secret_key = "daily-task-manager-key"

# File to store tasks permanently
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "tasks.json"
)


# Load saved tasks
def load_tasks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []
    return []


tasks = load_tasks()


# Save tasks to JSON
def save_tasks():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4)


# Find task by ID
def find_task(task_id):
    return next(
        (task for task in tasks if task["id"] == task_id),
        None
    )


# Dashboard
@app.route("/")
def home():
    search = request.args.get("search", "").strip().lower()
    status = request.args.get("status", "all")
    today = date.today().isoformat()

    filtered_tasks = [
        task for task in tasks
        if (
            search in task["title"].lower()
            or search in task.get("description", "").lower()
        )
        and (
            status == "all"
            or (status == "completed" and task["completed"])
            or (status == "pending" and not task["completed"])
        )
    ]

    # Sort incomplete tasks first, then by due date
    filtered_tasks.sort(
        key=lambda task: (task["completed"], task.get("due_date", ""))
    )

    return render_template(
        "index.html",
        tasks=filtered_tasks,
        total=len(tasks),
        completed=sum(task["completed"] for task in tasks),
        pending=sum(not task["completed"] for task in tasks),
        today=today,
        search=search,
        status=status,
        editing=None
    )


# Add a new task
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "Medium")

    if not title:
        flash("Task title is required.", "error")
        return redirect(url_for("home"))

    if priority not in ("Low", "Medium", "High"):
        priority = "Medium"

    new_id = max((task["id"] for task in tasks), default=0) + 1

    tasks.append({
        "id": new_id,
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "completed": False,
        "created_at": date.today().isoformat()
    })

    save_tasks()
    flash("Task added successfully!", "success")
    return redirect(url_for("home"))


# Edit an existing task
@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = find_task(task_id)

    if task is None:
        flash("Task not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "").strip()
        priority = request.form.get("priority", "Medium")

        if not title:
            flash("Task title is required.", "error")
            return redirect(url_for("edit_task", task_id=task_id))

        if priority not in ("Low", "Medium", "High"):
            priority = "Medium"

        task["title"] = title
        task["description"] = description
        task["due_date"] = due_date
        task["priority"] = priority

        save_tasks()
        flash("Task updated successfully!", "success")
        return redirect(url_for("home"))

    return render_template(
        "index.html",
        tasks=tasks,
        total=len(tasks),
        completed=sum(item["completed"] for item in tasks),
        pending=sum(not item["completed"] for item in tasks),
        today=date.today().isoformat(),
        search="",
        status="all",
        editing=task
    )


# Mark task completed or pending
@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    task = find_task(task_id)

    if task is None:
        flash("Task not found.", "error")
    else:
        task["completed"] = not task["completed"]
        save_tasks()
        flash("Task status updated!", "success")

    return redirect(url_for("home"))


# Delete task
@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = find_task(task_id)

    if task is None:
        flash("Task not found.", "error")
    else:
        tasks.remove(task)
        save_tasks()
        flash("Task deleted successfully!", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)