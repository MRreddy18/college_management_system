from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "college_management_secret"

DATABASE = "database.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            amount REAL,
            status TEXT,
            date TEXT
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

    # Default admin account
    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "Admin")
        )

    conn.commit()
    conn.close()


# ---------------- LOGIN REQUIRED ----------------

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)

    return wrapper


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
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


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------

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
        "SELECT COUNT(*) AS total FROM fees WHERE status='Pending'"
    ).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        students=students,
        faculty=faculty,
        announcements=announcements,
        fees_pending=fees_pending
    )


# ---------------- STUDENTS ----------------

@app.route("/students")
@login_required
def students():

    search = request.args.get("search", "")

    conn = get_db()

    if search:
        data = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ?
            OR department LIKE ?
            OR course LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

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

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        course = request.form["course"]
        department = request.form["department"]
        year = request.form["year"]

        conn = get_db()

        conn.execute("""
            INSERT INTO students
            (name, email, phone, course, department, year)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            course,
            department,
            year
        ))

        conn.commit()
        conn.close()

        flash("Student added successfully")

        return redirect(url_for("students"))

    return render_template("add_student.html")


@app.route("/students/delete/<int:id>")
@login_required
def delete_student(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM students WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Student deleted successfully")

    return redirect(url_for("students"))


# ---------------- FACULTY ----------------

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

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        designation = request.form["designation"]

        conn = get_db()

        conn.execute("""
            INSERT INTO faculty
            (name, email, phone, department, designation)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            department,
            designation
        ))

        conn.commit()
        conn.close()

        flash("Faculty added successfully")

        return redirect(url_for("faculty"))

    return render_template("add_faculty.html")


@app.route("/faculty/delete/<int:id>")
@login_required
def delete_faculty(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM faculty WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Faculty deleted successfully")

    return redirect(url_for("faculty"))


# ---------------- ATTENDANCE ----------------

@app.route("/attendance")
@login_required
def attendance():

    conn = get_db()

    data = conn.execute("""
        SELECT attendance.id,
               students.name,
               attendance.date,
               attendance.status
        FROM attendance
        JOIN students
        ON attendance.student_id = students.id
        ORDER BY attendance.id DESC
    """).fetchall()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        attendance=data,
        students=students
    )


@app.route("/attendance/add", methods=["POST"])
@login_required
def add_attendance():

    student_id = request.form["student_id"]
    date = request.form["date"]
    status = request.form["status"]

    conn = get_db()

    conn.execute("""
        INSERT INTO attendance
        (student_id, date, status)
        VALUES (?, ?, ?)
    """, (
        student_id,
        date,
        status
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("attendance"))


# ---------------- FEES ----------------

@app.route("/fees")
@login_required
def fees():

    conn = get_db()

    data = conn.execute("""
        SELECT fees.id,
               students.name,
               fees.amount,
               fees.status,
               fees.date
        FROM fees
        JOIN students
        ON fees.student_id = students.id
        ORDER BY fees.id DESC
    """).fetchall()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template(
        "fees.html",
        fees=data,
        students=students
    )


@app.route("/fees/add", methods=["POST"])
@login_required
def add_fee():

    student_id = request.form["student_id"]
    amount = request.form["amount"]
    status = request.form["status"]
    date = request.form["date"]

    conn = get_db()

    conn.execute("""
        INSERT INTO fees
        (student_id, amount, status, date)
        VALUES (?, ?, ?, ?)
    """, (
        student_id,
        amount,
        status,
        date
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("fees"))


# ---------------- ANNOUNCEMENTS ----------------

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


@app.route("/announcements/add", methods=["POST"])
@login_required
def add_announcement():

    title = request.form["title"]
    message = request.form["message"]
    date = request.form["date"]

    conn = get_db()

    conn.execute("""
        INSERT INTO announcements
        (title, message, date)
        VALUES (?, ?, ?)
    """, (
        title,
        message,
        date
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("announcements"))


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )