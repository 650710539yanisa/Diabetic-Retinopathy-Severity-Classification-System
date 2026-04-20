# ===== database.py =====
import sqlite3

DB_NAME = "users.db"

def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=10,          # ⭐ รอ lock ได้
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_db()

    # ===== USERS =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
    
        password TEXT NOT NULL
        
        -- role TEXT DEFAULT 'doctor',   -- doctor / admin
        -- active BOOLEAN DEFAULT 1,
        
        -- created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ===== DOCTOR PROFILE =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            hospital TEXT,
            license_no TEXT,
            specialization TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ===== PATIENTS =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
        
            hn TEXT NOT NULL,
            name TEXT NOT NULL,
        
            date_of_birth TEXT,
            gender TEXT,
        
            last_result TEXT,
            last_prediction_at TEXT,
        
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        
            FOREIGN KEY (doctor_id) REFERENCES users(id),
            UNIQUE (doctor_id, hn)
        )

    """)

    # ===== DIABETES INFO =====
    # ===== DIABETES INFO =====
    conn.execute("""
    CREATE TABLE IF NOT EXISTS diabetes_info (
        diabetes_id INTEGER PRIMARY KEY AUTOINCREMENT,

        patient_id INTEGER NOT NULL,

        diabetes_type TEXT
            CHECK(diabetes_type IN
            ('Type 1','Type 2','GDM','Secondary','MODY','Other')),

        diabetes_detail TEXT,   -- ⭐ เพิ่มรายละเอียด

        duration_years INTEGER,

        hba1c REAL,
        fbs REAL,
        rbs REAL,

        -- insulin BOOLEAN,
        -- oral_drug BOOLEAN,

        blood_pressure TEXT,

        -- dyslipidemia BOOLEAN,
        -- kidney_disease BOOLEAN,

        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    """)

    # ===== PREDICTIONS =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            image_path TEXT,
            result TEXT,
            confidence REAL,
            model_name TEXT,
            doctor_choice TEXT,
            eye TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    """)

    conn.commit()
    conn.close()
