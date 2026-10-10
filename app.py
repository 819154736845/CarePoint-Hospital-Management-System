from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-demo-secret-before-deployment")
DB_PATH = os.path.join(os.path.dirname(__file__), "hospital.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin'
        );
        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, age INTEGER, gender TEXT, phone TEXT, email TEXT,
            blood_group TEXT, address TEXT, medical_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS doctors(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            specialty TEXT NOT NULL, phone TEXT, email TEXT, room TEXT,
            availability TEXT DEFAULT 'Available'
        );
        CREATE TABLE IF NOT EXISTS appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL, appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL, reason TEXT, status TEXT NOT NULL DEFAULT 'Scheduled',
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE RESTRICT,
            FOREIGN KEY(doctor_id) REFERENCES doctors(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS bills(
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL,
            appointment_id INTEGER, description TEXT NOT NULL, amount REAL NOT NULL,
            paid REAL NOT NULL DEFAULT 0, bill_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Unpaid',
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
        );
        """)
        if not con.execute("SELECT id FROM users WHERE username='admin'").fetchone():
            con.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                        ("admin", generate_password_hash("admin123"), "admin"))
        if con.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
            con.executemany("INSERT INTO doctors(name,specialty,phone,email,room,availability) VALUES(?,?,?,?,?,?)", [
                ("Dr. Aanya Sharma","Cardiology","9876501001","aanya@careplus.demo","C-101","Available"),
                ("Dr. Rohan Mehta","Neurology","9876501002","rohan@careplus.demo","N-204","Available"),
                ("Dr. Sana Khan","Pediatrics","9876501003","sana@careplus.demo","P-110","On Leave"),
                ("Dr. Arjun Patel","Orthopedics","9876501004","arjun@careplus.demo","O-305","Available")
            ])
        if con.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            con.executemany("""INSERT INTO patients(patient_code,name,age,gender,phone,email,blood_group,address,medical_notes)
                VALUES(?,?,?,?,?,?,?,?,?)""", [
                ("PT-1001","Ishita Desai",28,"Female","9876502001","ishita@example.demo","B+","Nagpur, Maharashtra","Demo record"),
                ("PT-1002","Kabir Joshi",46,"Male","9876502002","kabir@example.demo","O+","Wardha, Maharashtra","Demo record"),
                ("PT-1003","Meera Kulkarni",35,"Female","9876502003","meera@example.demo","A-","Amravati, Maharashtra","Demo record")
            ])
        if con.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
            today = date.today().isoformat()
            con.execute("INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status) VALUES(1,1,?,?,?,?)",
                        (today,"10:30","Routine consultation","Scheduled"))
            con.execute("INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status) VALUES(2,2,?,?,?,?)",
                        (today,"12:00","Headache consultation","Scheduled"))
        if con.execute("SELECT COUNT(*) FROM bills").fetchone()[0] == 0:
            con.execute("INSERT INTO bills(patient_id,description,amount,paid,bill_date,status) VALUES(1,'Consultation fee',800,800,?,'Paid')",(date.today().isoformat(),))
            con.execute("INSERT INTO bills(patient_id,description,amount,paid,bill_date,status) VALUES(2,'Neurology consultation',1200,500,?,'Partial')",(date.today().isoformat(),))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year, "today": date.today().isoformat()}

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back. You are signed in.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    with db() as con:
        stats = {
            "patients": con.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "doctors": con.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            "appointments": con.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date=?", (date.today().isoformat(),)).fetchone()[0],
            "revenue": con.execute("SELECT COALESCE(SUM(paid),0) FROM bills").fetchone()[0],
            "pending": con.execute("SELECT COUNT(*) FROM appointments WHERE status='Scheduled'").fetchone()[0],
            "unpaid": con.execute("SELECT COALESCE(SUM(amount-paid),0) FROM bills").fetchone()[0]
        }
        upcoming = con.execute("""SELECT a.*, p.name patient_name, p.patient_code, d.name doctor_name, d.specialty
            FROM appointments a JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id
            ORDER BY CASE WHEN a.appointment_date < date('now') THEN 1 ELSE 0 END, a.appointment_date, a.appointment_time LIMIT 6""").fetchall()
        recent = con.execute("SELECT * FROM patients ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", stats=stats, upcoming=upcoming, recent=recent)

@app.route("/patients", methods=["GET","POST"])
@login_required
def patients():
    if request.method == "POST":
        f = request.form
        name = f.get("name","").strip()
        if not name:
            flash("Patient name is required.", "error")
            return redirect(url_for("patients"))
        with db() as con:
            next_id = con.execute("SELECT COALESCE(MAX(id),0)+1001 FROM patients").fetchone()[0]
            code = f"PT-{next_id}"
            con.execute("""INSERT INTO patients(patient_code,name,age,gender,phone,email,blood_group,address,medical_notes)
                VALUES(?,?,?,?,?,?,?,?,?)""", (code,name,f.get("age") or None,f.get("gender"),f.get("phone"),f.get("email"),f.get("blood_group"),f.get("address"),f.get("medical_notes")))
        flash(f"Patient registered successfully ({code}).", "success")
        return redirect(url_for("patients"))
    q = request.args.get("q","").strip()
    with db() as con:
        rows = con.execute("""SELECT * FROM patients WHERE name LIKE ? OR patient_code LIKE ? OR phone LIKE ? ORDER BY id DESC""",
                           (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    return render_template("patients.html", patients=rows, q=q)

@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    with db() as con:
        patient = con.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients"))
        appointments = con.execute("""SELECT a.*,d.name doctor_name,d.specialty FROM appointments a JOIN doctors d ON d.id=a.doctor_id
            WHERE a.patient_id=? ORDER BY a.appointment_date DESC,a.appointment_time DESC""",(patient_id,)).fetchall()
        bills = con.execute("SELECT * FROM bills WHERE patient_id=? ORDER BY id DESC",(patient_id,)).fetchall()
    return render_template("patient_detail.html", patient=patient, appointments=appointments, bills=bills)

@app.route("/doctors", methods=["GET","POST"])
@login_required
def doctors():
    if request.method == "POST":
        f=request.form
        name=f.get("name","").strip(); specialty=f.get("specialty","").strip()
        if not name or not specialty:
            flash("Doctor name and specialty are required.", "error")
        else:
            with db() as con:
                con.execute("INSERT INTO doctors(name,specialty,phone,email,room,availability) VALUES(?,?,?,?,?,?)",
                            (name,specialty,f.get("phone"),f.get("email"),f.get("room"),f.get("availability","Available")))
            flash("Doctor added successfully.", "success")
        return redirect(url_for("doctors"))
    q=request.args.get("q","").strip()
    with db() as con:
        rows=con.execute("SELECT * FROM doctors WHERE name LIKE ? OR specialty LIKE ? OR room LIKE ? ORDER BY name",
                         (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    return render_template("doctors.html", doctors=rows, q=q)

@app.route("/appointments", methods=["GET","POST"])
@login_required
def appointments():
    if request.method == "POST":
        f=request.form
        try:
            with db() as con:
                con.execute("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                    VALUES(?,?,?,?,?,?)""", (int(f["patient_id"]),int(f["doctor_id"]),f["appointment_date"],f["appointment_time"],f.get("reason"),"Scheduled"))
            flash("Appointment booked successfully.", "success")
        except (ValueError, KeyError, sqlite3.IntegrityError):
            flash("Please choose a valid patient, doctor, date and time.", "error")
        return redirect(url_for("appointments"))
    q=request.args.get("q","").strip()
    with db() as con:
        patients_list=con.execute("SELECT id,patient_code,name FROM patients ORDER BY name").fetchall()
        doctors_list=con.execute("SELECT id,name,specialty FROM doctors WHERE availability='Available' ORDER BY name").fetchall()
        rows=con.execute("""SELECT a.*,p.name patient_name,p.patient_code,d.name doctor_name,d.specialty
            FROM appointments a JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id
            WHERE p.name LIKE ? OR d.name LIKE ? OR a.status LIKE ? ORDER BY a.appointment_date DESC,a.appointment_time DESC""",
            (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    return render_template("appointments.html", appointments=rows, patients=patients_list, doctors=doctors_list, q=q)

@app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@login_required
def appointment_status(appointment_id):
    status=request.form.get("status")
    if status not in ("Scheduled","Completed","Cancelled"):
        flash("Invalid appointment status.", "error")
    else:
        with db() as con:
            con.execute("UPDATE appointments SET status=? WHERE id=?", (status,appointment_id))
        flash("Appointment status updated.", "success")
    return redirect(request.referrer or url_for("appointments"))

@app.route("/billing", methods=["GET","POST"])
@login_required
def billing():
    if request.method == "POST":
        f=request.form
        try:
            patient_id=int(f["patient_id"]); amount=float(f["amount"]); paid=float(f.get("paid") or 0)
            if amount <= 0 or paid < 0 or paid > amount: raise ValueError()
            status="Paid" if paid == amount else ("Partial" if paid > 0 else "Unpaid")
            with db() as con:
                con.execute("INSERT INTO bills(patient_id,description,amount,paid,bill_date,status) VALUES(?,?,?,?,?,?)",
                            (patient_id,f.get("description","Hospital service").strip(),amount,paid,f.get("bill_date") or date.today().isoformat(),status))
            flash("Bill created successfully.", "success")
        except (ValueError, KeyError, sqlite3.IntegrityError):
            flash("Check patient and enter valid amounts. Paid amount cannot exceed total.", "error")
        return redirect(url_for("billing"))
    q=request.args.get("q","").strip()
    with db() as con:
        patients_list=con.execute("SELECT id,name,patient_code FROM patients ORDER BY name").fetchall()
        bills=con.execute("""SELECT b.*,p.name patient_name,p.patient_code FROM bills b JOIN patients p ON p.id=b.patient_id
            WHERE p.name LIKE ? OR p.patient_code LIKE ? OR b.description LIKE ? ORDER BY b.id DESC""",
            (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
        totals=con.execute("SELECT COALESCE(SUM(amount),0) total,COALESCE(SUM(paid),0) paid FROM bills").fetchone()
    return render_template("billing.html", bills=bills, patients=patients_list, q=q, totals=totals)

@app.route("/billing/<int:bill_id>/pay", methods=["POST"])
@login_required
def pay_bill(bill_id):
    try:
        payment=float(request.form.get("payment","0"))
        with db() as con:
            bill=con.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
            if not bill or payment <= 0 or payment > bill["amount"]-bill["paid"]:
                flash("Enter a valid payment amount.", "error")
            else:
                paid=bill["paid"]+payment
                status="Paid" if paid >= bill["amount"] else "Partial"
                con.execute("UPDATE bills SET paid=?,status=? WHERE id=?", (paid,status,bill_id))
                flash("Payment recorded.", "success")
    except ValueError:
        flash("Enter a valid number.", "error")
    return redirect(url_for("billing"))

@app.route("/search")
@login_required
def search():
    q=request.args.get("q","").strip()
    if not q: return render_template("search.html", q=q, patients=[], doctors=[], appointments=[])
    like=f"%{q}%"
    with db() as con:
        ps=con.execute("SELECT * FROM patients WHERE name LIKE ? OR patient_code LIKE ? OR phone LIKE ?",(like,like,like)).fetchall()
        ds=con.execute("SELECT * FROM doctors WHERE name LIKE ? OR specialty LIKE ?",(like,like)).fetchall()
        aps=con.execute("""SELECT a.*,p.name patient_name,d.name doctor_name FROM appointments a JOIN patients p ON p.id=a.patient_id JOIN doctors d ON d.id=a.doctor_id
            WHERE p.name LIKE ? OR d.name LIKE ? OR a.reason LIKE ?""",(like,like,like)).fetchall()
    return render_template("search.html", q=q, patients=ps, doctors=ds, appointments=aps)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
