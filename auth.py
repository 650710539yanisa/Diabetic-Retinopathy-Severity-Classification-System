from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import re

auth_bp = Blueprint("auth", __name__)

# ================= ROOT =================
@auth_bp.route("/")
def root():
    return redirect(url_for("auth.dashboard"))

# ================= DASHBOARD =================
from datetime import date


@auth_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    # ===== Total Patients (ของหมอคนนี้) =====
    total_patients = db.execute("""
        SELECT COUNT(*) 
        FROM patients
        WHERE doctor_id = ?
    """, (session["user_id"],)).fetchone()[0]


    # ===== Predictions Today =====
    today = date.today()

    today_predictions = db.execute("""
        SELECT COUNT(*) 
        FROM predictions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE DATE(pr.created_at)=?
          AND p.doctor_id = ?
    """, (today, session["user_id"])).fetchone()[0]


    # ===== Moderate+ DR =====
    moderate_plus = db.execute("""
        SELECT COUNT(*) 
        FROM predictions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE pr.result IN ('Moderate','Severe','Proliferative')
          AND p.doctor_id = ?
    """, (session["user_id"],)).fetchone()[0]


    # ===== Follow-up Needed =====
    follow_up = db.execute("""
        SELECT COUNT(*) 
        FROM predictions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE pr.result IN ('Severe','Proliferative')
          AND p.doctor_id = ?
    """, (session["user_id"],)).fetchone()[0]


    # ===== Recent Predictions =====
    recent = db.execute("""
        SELECT 
            p.hn,
            p.name,
            pr.result,
            pr.created_at

        FROM predictions pr
        JOIN patients p ON pr.patient_id = p.id

        WHERE p.doctor_id = ?

        ORDER BY pr.created_at DESC
        LIMIT 5
    """, (session["user_id"],)).fetchall()


    return render_template(
        "dashboard.html",

        total_patients=total_patients,
        today_predictions=today_predictions,
        moderate_plus=moderate_plus,
        follow_up=follow_up,

        recent=recent
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("""
            SELECT u.id, u.username, u.password, d.full_name
            FROM users u
            LEFT JOIN doctor_profiles d ON u.id = d.user_id
            WHERE u.username=?
        """, (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            return redirect(url_for("auth.dashboard"))

        flash("❌ Invalid username or password")

    return render_template("login.html")



@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

# ================= DOCTOR PROFILE =================
# ===== DOCTOR PROFILE =====
@auth_bp.route("/doctor/profile")
def doctor_profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db()

    doctor = conn.execute("""
        SELECT * FROM doctor_profiles
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    return render_template("doctor_profile.html", doctor=doctor)

# ================= PREDICT =================

# ไม่รู้ hn

# ================= PATIENTS =================
# @auth_bp.route("/patients")
# def patients():
#     if "user_id" not in session:
#         return redirect(url_for("auth.login"))
#
#     patients = [
#         {"hn": "HN001", "name": "Somchai", "age": 58, "result": "Moderate"},
#         {"hn": "012", "name": "Suda", "age": 47, "result": "Mild"},
#     ]
#     return render_template("patients.html", patients=patients)
#
@auth_bp.route("/patients")
def patients():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    patients = db.execute("""
        SELECT 
            p.*,
            MAX(pr.created_at) AS last_visit
        FROM patients p
        LEFT JOIN predictions pr 
            ON p.id = pr.patient_id
        WHERE p.doctor_id = ?
        GROUP BY p.id
        ORDER BY last_visit DESC
    """, (session["user_id"],)).fetchall()

    return render_template("patients.html", patients=patients)

@auth_bp.route("/new_patient", methods=["GET","POST"])
def new_patient():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":

        # ================= PATIENT =================

        hn = request.form["hn"]
        name = request.form["name"]
        dob = request.form["date_of_birth"]
        gender = request.form["gender"]

        doctor_id = session["user_id"]
        diabetes_type = request.form.get("diabetes_type")
        errors = {}
        # ===== VALIDATION =====

        if not diabetes_type:
            errors["diabetes_type"] = "Please select diabetes type"

        if not hn:
            errors["hn"] = "Please enter HN"

        if not name:
            errors["name"] = "Please enter full name"

        if not dob:
            errors["date_of_birth"] = "Please select date of birth"

        if not gender:
            errors["gender"] = "Please select gender"

        # เช็ค HN ซ้ำ
        exist = db.execute("""
                    SELECT 1 FROM patients
                    WHERE hn=? AND doctor_id=?
                """, (hn, doctor_id)).fetchone()

        if exist:
            errors["hn"] = "This HN already exists"

        # ❗ ถ้ามี error → กลับหน้าเดิม
        if errors:
            return render_template(
                "new_patient.html",
                errors=errors,
                patient=request.form,  # 🔥 ใช้แทน form
                diabetes=request.form,
                button_label="Save Patient",
                cancel_url=url_for("auth.patients")
            )

        cur = db.cursor()

        # Insert patient
        cur.execute("""
        INSERT INTO patients
        (hn, name, date_of_birth, gender, doctor_id)

        VALUES (?,?,?,?,?)
        """, (hn, name, dob, gender, doctor_id))


        patient_id = cur.lastrowid   # ID คนไข้


        # ================= DIABETES =================

        diabetes_type = request.form.get("diabetes_type")
        diabetes_detail = request.form.get("diabetes_detail")
        duration = request.form.get("duration_years")
        hba1c = request.form.get("hba1c")
        fbs = request.form.get("fbs")
        rbs = request.form.get("rbs")
        bp = request.form.get("blood_pressure")
        # insulin = request.form.get("insulin")
        # oral = request.form.get("oral_drug")
        #
        # insulin = int(insulin) if insulin in ["0", "1"] else None
        # oral = int(oral) if oral in ["0", "1"] else None
        # dys = 1 if request.form.get("dyslipidemia") else 0
        # kidney = 1 if request.form.get("kidney_disease") else 0


        # Insert diabetes_info
        cur.execute("""
        INSERT INTO diabetes_info
        (
         patient_id,
         diabetes_type,
         diabetes_detail,
         duration_years,

         hba1c, fbs, rbs,
         insulin, oral_drug,
         blood_pressure,
         dyslipidemia, kidney_disease
        )

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            patient_id,
            diabetes_type,
            diabetes_detail,
            duration,
            hba1c,
            fbs,
            rbs

        ))

        db.commit()
        db.close()  # ⭐ เพิ่มบรรทัดนี้

        return redirect(url_for("auth.patients"))

    return render_template(
        "new_patient.html",
        patient=None,
        diabetes=None,
        button_label="Save Patient",
        cancel_url=url_for("auth.patients")
    )


@auth_bp.route("/patient/<hn>")
def patient_detail(hn):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    # Patient
    patient = db.execute("""
        SELECT *
        FROM patients
        WHERE hn = ? AND doctor_id = ?
    """, (hn, session["user_id"])).fetchone()


    # Diabetes
    diabetes = db.execute("""
        SELECT *
        FROM diabetes_info
        WHERE patient_id = ?
        ORDER BY diabetes_id DESC
        LIMIT 1
    """, (patient["id"],)).fetchone()


    # History
    history = db.execute("""
        SELECT *
        FROM predictions
        WHERE patient_id = ?
        ORDER BY created_at DESC
    """, (patient["id"],)).fetchall()


    return render_template(
        "patient_detail.html",
        patient=patient,
        diabetes=diabetes,
        history=history
    )


@auth_bp.route("/patients/<hn>/predict")
def new_prediction(hn):
    db = get_db()
    patient = db.execute(
        "SELECT * FROM patients WHERE hn = ?",
        (hn,)
    ).fetchone()

    return render_template(
        "index.html",
        patient=patient,
        logged_in=("user_id" in session)
    )

# ================= HISTORY =================
@auth_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    history = db.execute("""
        SELECT
            p.hn,
            p.name,
            pr.eye,
            pr.result,
            pr.confidence,
            pr.model_name AS model,
            pr.created_at AS date
        FROM predictions pr
        JOIN patients p ON pr.patient_id = p.id
        WHERE p.doctor_id = ?
        ORDER BY pr.created_at DESC
    """, (session["user_id"],)).fetchall()

    return render_template("history.html", history=history)


from PIL import Image
import numpy as np
from flask import jsonify, request, session
from model_loader import MODELS
from ml_models import severity_labels
import os
import time

@auth_bp.route("/api/predict", methods=["POST"])
def api_predict():

    print("========== PREDICT DEBUG ==========")

    print("SESSION USER:", session.get("user_id"))

    if "image" not in request.files:
        print("❌ No image")
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]

    eye = request.form.get("eye")
    patient_hn = request.form.get("hn")

    print("HN:", patient_hn)
    print("EYE:", eye)

    img = Image.open(file).convert("RGB")

    rows = []
    best = {"conf": 0}

    for name, obj in MODELS.items():

        x = img.resize((224, 224))
        x = np.array(x)
        x = np.expand_dims(x, axis=0)

        x2 = obj["preprocess"](x.copy())

        pred = obj["model"].predict(x2, verbose=0)[0]

        cls = int(np.argmax(pred))
        conf = float(np.max(pred))

        if conf > best["conf"]:
            best = {
                "label": severity_labels[cls],
                "conf": conf,
                "model": name
            }

        rows.append({
            "model": name,
            "label": severity_labels[cls],
            "conf": round(conf, 4)
        })


    # ===== DEBUG SAVE =====

    if "user_id" not in session:
        print("❌ NOT LOGIN")

    elif not patient_hn:
        print("❌ NO HN SENT")

    else:

        db = get_db()

        patient = db.execute(
            "SELECT id FROM patients WHERE hn=? AND doctor_id=?",
            (patient_hn, session["user_id"])
        ).fetchone()

        print("PATIENT:", patient)

        if not patient:
            print("❌ PATIENT NOT FOUND")

        else:
            print("✅ READY TO SAVE")

            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)

            filename = f"{patient_hn}_{eye}_{int(time.time())}.jpg"
            relative_path = f"uploads/{filename}"
            filepath = os.path.join("static", relative_path)

            img.save(filepath)

            db.execute("""
                INSERT INTO predictions
                (patient_id, image_path, result, confidence, model_name, eye)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                patient["id"],
                relative_path,
                best["label"],
                best["conf"],
                best["model"],
                eye
            ))

            db.execute("""
                UPDATE patients
                SET last_result=?, last_prediction_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (best["label"], patient["id"]))

            db.commit()

            print("✅ SAVED SUCCESS")


    return jsonify({
        "rows": rows,
        "best": best
    })


@auth_bp.route("/edit_patient/<hn>", methods=["GET", "POST"])
def edit_patient(hn):

    db = get_db()

    patient = db.execute("""
        SELECT * FROM patients 
        WHERE hn = ? AND doctor_id = ?
    """, (hn, session["user_id"])).fetchone()

    diabetes = db.execute(
        "SELECT * FROM diabetes_info WHERE patient_id = ?",
        (patient["id"],)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["date_of_birth"]
        gender = request.form["gender"]

        diabetes_type = request.form["diabetes_type"]
        duration = request.form["duration_years"]
        hba1c = request.form["hba1c"]

        # ⭐ เพิ่มตรงนี้
        insulin = request.form.get("insulin")
        oral = request.form.get("oral_drug")

        insulin = int(insulin) if insulin in ["0", "1"] else None
        oral = int(oral) if oral in ["0", "1"] else None

        # update patient
        db.execute("""
            UPDATE patients
            SET name=?, date_of_birth=?, gender=?
            WHERE hn=?
        """, (name, dob, gender, hn))

        # update diabetes
        db.execute("""
            UPDATE diabetes_info
            SET diabetes_type=?,
                duration_years=?,
                hba1c=?,
                insulin=?,
                oral_drug=?
            WHERE patient_id=?
        """, (
            diabetes_type,
            duration,
            hba1c,
            insulin,
            oral,
            patient["id"]
        ))

        db.commit()

        return redirect(url_for("auth.patient_detail", hn=hn))

    return render_template(
        "edit_patient.html",
        patient=patient,
        diabetes=diabetes,
        button_label="Update Patient",
        cancel_url=url_for("auth.patient_detail", hn=hn)
    )

@auth_bp.route("/api/doctor_choice", methods=["POST"])
def doctor_choice():

    data = request.get_json()

    model = data.get("model")
    hn = data.get("hn")

    db = get_db()

    patient = db.execute(
        "SELECT id FROM patients WHERE hn=? AND doctor_id=?",
        (hn, session["user_id"])
    ).fetchone()

    if not patient:
        return jsonify({"error":"patient not found"}),404


    # ===== หา prediction ล่าสุด =====
    pred = db.execute("""
        SELECT id
        FROM predictions
        WHERE patient_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """,(patient["id"],)).fetchone()


    if pred:

        db.execute("""
            UPDATE predictions
            SET doctor_choice = ?
            WHERE id = ?
        """,(model,pred["id"]))

        db.commit()

    return jsonify({"status":"ok"})


@auth_bp.route("/doctor/edit", methods=["GET", "POST"])
def edit_doctor():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    doctor = db.execute("""
        SELECT * FROM doctor_profiles
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    if request.method == "POST":
        full_name = request.form["full_name"]
        hospital = request.form["hospital"]
        license_no = request.form["license_no"]
        specialization = request.form["specialization"]

        db.execute("""
            UPDATE doctor_profiles
            SET full_name=?, hospital=?, license_no=?, specialization=?
            WHERE user_id=?
        """, (full_name, hospital, license_no, specialization, session["user_id"]))

        db.commit()

        # ⭐⭐⭐ ตรงนี้แหละที่คุณขาด!
        session["full_name"] = full_name

        return redirect(url_for("auth.doctor_profile"))

    return render_template("edit_doctor.html", doctor=doctor)