from flask import Flask, jsonify
from flask_cors import CORS
import pymysql
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'), # assuming root
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'HOSPITAL_HMS'),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/api/dashboard-stats')
def get_stats():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total_patients FROM Patient")
            patients = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as total_doctors FROM Doctor")
            doctors = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as total_appointments FROM Appointment")
            appointments = cursor.fetchone()
            
        conn.close()
        return jsonify({
            "patients": patients['total_patients'] if patients else 0,
            "doctors": doctors['total_doctors'] if doctors else 0,
            "appointments": appointments['total_appointments'] if appointments else 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/doctors')
def get_doctors():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.doctor_id, d.name as doctor_name, d.specialization, dept.name as department_name
                FROM Doctor d
                LEFT JOIN Department dept ON d.department_id = dept.department_id
                LIMIT 10
            """)
            doctors = cursor.fetchall()
        conn.close()
        return jsonify({"doctors": doctors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/appointments')
def get_recent_appointments():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.appointment_id, p.name as patient_name, d.name as doctor_name, a.date, a.status
                FROM Appointment a
                JOIN Patient p ON a.patient_id = p.patient_id
                JOIN Doctor d ON a.doctor_id = d.doctor_id
                ORDER BY a.date DESC
                LIMIT 5
            """)
            appointments = cursor.fetchall()
            for appt in appointments:
                if appt.get('date'):
                    appt['date'] = str(appt['date'])
        conn.close()
        return jsonify({"appointments": appointments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a default fallback route for testing
@app.route('/api')
def api_root():
    return jsonify({"message": "Hospital HMS API is running!"})

if __name__ == '__main__':
    app.run(port=5333, debug=True)
