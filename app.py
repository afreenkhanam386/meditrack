from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql
import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

# ── Dashboard ──────────────────────────────────────────────
@app.route("/")
def dashboard():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM equipment")
        total = cur.fetchone()["total"]

        cur.execute("SELECT status, COUNT(*) AS count FROM equipment GROUP BY status")
        by_status = cur.fetchall()

        cur.execute("""
            SELECT e.equipment_name, e.serial_number, e.department, m.next_due_date
            FROM maintenance_log m
            JOIN equipment e ON e.equipment_id = m.equipment_id
            WHERE m.next_due_date < CURDATE()
        """)
        overdue = cur.fetchall()
    db.close()
    return render_template("dashboard.html", total=total, by_status=by_status, overdue=overdue)

# ── Equipment List ─────────────────────────────────────────
@app.route("/equipment")
def equipment_list():
    dept   = request.args.get("department", "")
    status = request.args.get("status", "")
    db = get_db()
    with db.cursor() as cur:
        query = "SELECT * FROM equipment WHERE 1=1"
        params = []
        if dept:
            query += " AND department = %s"; params.append(dept)
        if status:
            query += " AND status = %s"; params.append(status)
        cur.execute(query, params)
        equipment = cur.fetchall()

        cur.execute("SELECT DISTINCT department FROM equipment")
        departments = [r["department"] for r in cur.fetchall()]
    db.close()
    return render_template("equipment_list.html", equipment=equipment,
                           departments=departments, selected_dept=dept, selected_status=status)

# ── Add Equipment ──────────────────────────────────────────
@app.route("/equipment/add", methods=["GET", "POST"])
def add_equipment():
    if request.method == "POST":
        db = get_db()
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO equipment (equipment_name, serial_number, department, purchase_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                request.form["equipment_name"],
                request.form["serial_number"],
                request.form["department"],
                request.form["purchase_date"],
                request.form["status"]
            ))
        db.commit(); db.close()
        return redirect(url_for("equipment_list"))
    return render_template("add_equipment.html")

# ── Update Status ──────────────────────────────────────────
@app.route("/equipment/<int:eid>/status", methods=["POST"])
def update_status(eid):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE equipment SET status=%s WHERE equipment_id=%s",
                    (request.form["status"], eid))
    db.commit(); db.close()
    return redirect(url_for("equipment_list"))

# ── Maintenance History ────────────────────────────────────
@app.route("/equipment/<int:eid>/history")
def maintenance_history(eid):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM equipment WHERE equipment_id=%s", (eid,))
        equip = cur.fetchone()
        cur.execute("SELECT * FROM maintenance_log WHERE equipment_id=%s ORDER BY maintenance_date DESC", (eid,))
        logs = cur.fetchall()
    db.close()
    return render_template("maintenance_history.html", equip=equip, logs=logs)

# ── Add Maintenance Log ────────────────────────────────────
@app.route("/equipment/<int:eid>/log/add", methods=["GET", "POST"])
def add_log(eid):
    if request.method == "POST":
        db = get_db()
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO maintenance_log
                  (equipment_id, maintenance_date, technician_name, issue_reported, resolution_notes, next_due_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                eid,
                request.form["maintenance_date"],
                request.form["technician_name"],
                request.form["issue_reported"],
                request.form["resolution_notes"],
                request.form["next_due_date"]
            ))
        db.commit(); db.close()
        return redirect(url_for("maintenance_history", eid=eid))
    return render_template("add_log.html", eid=eid)

# ── Stretch: Overdue JSON API ──────────────────────────────
@app.route("/api/overdue")
def overdue_api():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT e.equipment_id, e.equipment_name, e.serial_number,
                   e.department, m.next_due_date
            FROM maintenance_log m
            JOIN equipment e ON e.equipment_id = m.equipment_id
            WHERE m.next_due_date < CURDATE()
        """)
        rows = cur.fetchall()
    db.close()
    for r in rows:
        if r.get("next_due_date"):
            r["next_due_date"] = str(r["next_due_date"])
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)
