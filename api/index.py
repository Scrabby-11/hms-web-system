from flask import Flask, jsonify, request
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
                SELECT d.doctor_id, d.name as doctor_name, d.specialization, dept.name as department_name, d.phone_no, d.email
                FROM Doctor d
                LEFT JOIN Department dept ON d.department_id = dept.department_id
            """)
            doctors = cursor.fetchall()
        conn.close()
        return jsonify({"doctors": doctors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients')
def get_patients():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT patient_id, name, gender, dob, phone_no, address
                FROM Patient
                ORDER BY patient_id DESC
            """)
            patients = cursor.fetchall()
            for p in patients:
                if p.get('dob'): p['dob'] = str(p['dob'])
        conn.close()
        return jsonify({"patients": patients})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/appointments', methods=['GET', 'POST'])
def manage_appointments():
    if request.method == 'GET':
        limit = request.args.get('limit')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                query = """
                    SELECT a.appointment_id, p.name as patient_name, d.name as doctor_name, a.date, a.time, a.status
                    FROM Appointment a
                    JOIN Patient p ON a.patient_id = p.patient_id
                    JOIN Doctor d ON a.doctor_id = d.doctor_id
                    ORDER BY a.appointment_id DESC
                """
                if limit:
                    query += f" LIMIT {int(limit)}"
                cursor.execute(query)
                appointments = cursor.fetchall()
                for appt in appointments:
                    if appt.get('date'): appt['date'] = str(appt['date'])
                    if appt.get('time'): appt['time'] = str(appt['time'])
            conn.close()
            return jsonify({"appointments": appointments})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        data = request.json
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(appointment_id) as max_id FROM Appointment")
                row = cursor.fetchone()
                next_id = (row['max_id'] or 0) + 1
                
                cursor.execute("""
                    INSERT INTO Appointment (appointment_id, patient_id, doctor_id, date, time, status)
                    VALUES (%s, %s, %s, %s, %s, 'Pending')
                """, (next_id, data['patient_id'], data['doctor_id'], data['date'], data['time']))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Appointment created successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api')
def api_root():
    return jsonify({"message": "Hospital HMS API is running!"})

if __name__ == '__main__':
    app.run(port=5333, debug=True)
