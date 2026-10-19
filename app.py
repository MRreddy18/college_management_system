from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-for-local-testing"
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "database.db"
)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            course TEXT,
            department TEXT,
            year TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            designation TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY (student_id)
                REFERENCES students(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            amount REAL,
            status TEXT,
            date TEXT,
            FOREIGN KEY (student_id)
                REFERENCES students(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            message TEXT,
            date TEXT
        )
    """)

    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "Admin")
        )

    conn.commit()
    conn.close()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return wrapper


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    students = conn.execute(
        "SELECT COUNT(*) AS total FROM students"
    ).fetchone()["total"]

    faculty = conn.execute(
        "SELECT COUNT(*) AS total FROM faculty"
    ).fetchone()["total"]

    announcements = conn.execute(
        "SELECT COUNT(*) AS total FROM announcements"
    ).fetchone()["total"]

    fees_pending = conn.execute(
        "SELECT COUNT(*) AS total FROM fees WHERE status = ?",
        ("Pending",)
    ).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        students=students,
        faculty=faculty,
        announcements=announcements,
        fees_pending=fees_pending
    )
# STUDENTS
@app.route("/students")
@login_required
def students():
    search = request.args.get("search", "").strip()

    conn = get_db()

    if search:
        pattern = f"%{search}%"

        data = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ?
            OR department LIKE ?
            OR course LIKE ?
            ORDER BY id DESC
        """, (pattern, pattern, pattern)).fetchall()

    else:
        data = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=data,
        search=search
    )


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        values = (
            request.form.get("name", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("course", "").strip(),
            request.form.get("department", "").strip(),
            request.form.get("year", "").strip()
        )

        if not values[0]:
            flash("Student name is required")
            return redirect(url_for("add_student"))

        conn = get_db()

        conn.execute("""
            INSERT INTO students
            (name, email, phone, course, department, year)
            VALUES (?, ?, ?, ?, ?, ?)
        """, values)

        conn.commit()
        conn.close()

        flash("Student added successfully")
        return redirect(url_for("students"))

    return render_template("add_student.html")


@app.route("/students/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_student(id):
    conn = get_db()

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Student deleted successfully")
    return redirect(url_for("students"))


# FACULTY
@app.route("/faculty")
@login_required
def faculty():
    conn = get_db()

    data = conn.execute(
        "SELECT * FROM faculty ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "faculty.html",
        faculty=data
    )


@app.route("/faculty/add", methods=["GET", "POST"])
@login_required
def add_faculty():
    if request.method == "POST":
        values = (
            request.form.get("name", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("department", "").strip(),
            request.form.get("designation", "").strip()
        )

        if not values[0]:
            flash("Faculty name is required")
            return redirect(url_for("add_faculty"))

        conn = get_db()

        conn.execute("""
            INSERT INTO faculty
            (name, email, phone, department, designation)
            VALUES (?, ?, ?, ?, ?)
        """, values)

        conn.commit()
        conn.close()

        flash("Faculty added successfully")
        return redirect(url_for("faculty"))

    return render_template("add_faculty.html")


@app.route("/faculty/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_faculty(id):
    conn = get_db()

    conn.execute(
        "DELETE FROM faculty WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Faculty deleted successfully")
    return redirect(url_for("faculty"))


# ATTENDANCE
@app.route("/attendance")
@login_required
def attendance():
    conn = get_db()

    data = conn.execute("""
        SELECT attendance.id,
               attendance.student_id,
               students.name,
               attendance.date,
               attendance.status
        FROM attendance
        LEFT JOIN students
        ON attendance.student_id = students.id
        ORDER BY attendance.id DESC
    """).fetchall()

    student_list = conn.execute(
        "SELECT id, name FROM students ORDER BY name"
    ).fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        attendance=data,
        students=student_list
    )


@app.route("/attendance/add", methods=["POST"])
@login_required
def add_attendance():
    student_id = request.form.get("student_id", type=int)
    attendance_date = (
        request.form.get("date") or date.today().isoformat()
    )
    status = request.form.get("status", "Present").strip()

    if not student_id:
        flash("Please select a student")
        return redirect(url_for("attendance"))

    conn = get_db()

    conn.execute("""
        INSERT INTO attendance (student_id, date, status)
        VALUES (?, ?, ?)
    """, (student_id, attendance_date, status))

    conn.commit()
    conn.close()

    flash("Attendance saved successfully")
    return redirect(url_for("attendance"))
# FEES
@app.route("/fees")
@login_required
def fees():
    conn = get_db()

    data = conn.execute("""
        SELECT fees.id,
               fees.student_id,
               students.name AS student_name,
               fees.amount,
               fees.status,
               fees.date
        FROM fees
        LEFT JOIN students
        ON fees.student_id = students.id
        ORDER BY fees.id DESC
    """).fetchall()

    student_list = conn.execute(
        "SELECT id, name FROM students ORDER BY name"
    ).fetchall()

    conn.close()

    return render_template(
        "fees.html",
        fees=data,
        students=student_list
    )


@app.route("/fees/add", methods=["POST"])
@login_required
def add_fee():
    student_id = request.form.get("student_id", type=int)
    amount = request.form.get("amount", type=float)
    status = request.form.get("status", "Pending").strip()
    fee_date = request.form.get("date") or date.today().isoformat()

    if not student_id or amount is None:
        flash("Please select a student and enter a valid amount")
        return redirect(url_for("fees"))

    conn = get_db()

    conn.execute("""
        INSERT INTO fees (student_id, amount, status, date)
        VALUES (?, ?, ?, ?)
    """, (student_id, amount, status, fee_date))

    conn.commit()
    conn.close()

    flash("Fee record added successfully")
    return redirect(url_for("fees"))


# ANNOUNCEMENTS
@app.route("/announcements")
@login_required
def announcements():
    conn = get_db()

    data = conn.execute(
        "SELECT * FROM announcements ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "announcements.html",
        announcements=data
    )


@app.route("/announcements/add", methods=["GET", "POST"])
@login_required
def add_announcement():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        announcement_date = (
            request.form.get("date") or date.today().isoformat()
        )

        if not title or not message:
            flash("Please enter both a title and message")
            return redirect(url_for("add_announcement"))

        conn = get_db()

        conn.execute("""
            INSERT INTO announcements (title, message, date)
            VALUES (?, ?, ?)
        """, (title, message, announcement_date))

        conn.commit()
        conn.close()

        flash("Announcement published successfully")
        return redirect(url_for("announcements"))

    return render_template("add_announcement.html")


@app.route("/announcements/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_announcement(id):
    conn = get_db()

    conn.execute(
        "DELETE FROM announcements WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Announcement deleted successfully")
    return redirect(url_for("announcements"))


# CREATE DATABASE TABLES
init_db()


if __name__ == "__main__":
    app.run(debug=True) 