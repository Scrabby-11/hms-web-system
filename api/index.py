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

@app.route('/api/doctors', methods=['GET', 'POST'])
def manage_doctors():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT d.doctor_id, d.name as doctor_name, d.specialization, dept.name as department_name, d.phone_no, d.email
                    FROM Doctor d
                    LEFT JOIN Department dept ON d.department_id = dept.department_id
                    ORDER BY d.doctor_id DESC
                """)
                doctors = cursor.fetchall()
            conn.close()
            return jsonify({"doctors": doctors})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        data = request.json
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(doctor_id) as max_id FROM Doctor")
                row = cursor.fetchone()
                next_id = (row['max_id'] or 0) + 1
                
                cursor.execute("""
                    INSERT INTO Doctor (doctor_id, department_id, name, specialization, phone_no, email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (next_id, 1, data['name'], data.get('specialization', 'General'), data.get('phone_no', ''), data.get('email', '')))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Doctor added successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Appointment WHERE doctor_id = %s", (doctor_id,))
            cursor.execute("DELETE FROM Doctor WHERE doctor_id = %s", (doctor_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Doctor deleted successfully!"})
    except Exception as e:
        return jsonify({"error": "Cannot delete doctor: " + str(e)}), 500

@app.route('/api/patients', methods=['GET', 'POST'])
def manage_patients():
    if request.method == 'GET':
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
            
    if request.method == 'POST':
        data = request.json
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(patient_id) as max_id FROM Patient")
                row = cursor.fetchone()
                next_id = (row['max_id'] or 0) + 1
                
                cursor.execute("""
                    INSERT INTO Patient (patient_id, name, gender, dob, phone_no, address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (next_id, data['name'], data.get('gender', 'Male'), data.get('dob') or None, data.get('phone_no', ''), data.get('address', '')))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Patient added successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Appointment WHERE patient_id = %s", (patient_id,))
            cursor.execute("DELETE FROM Patient WHERE patient_id = %s", (patient_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Patient deleted successfully!"})
    except Exception as e:
        return jsonify({"error": "Cannot delete patient: " + str(e)}), 500

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

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Appointment WHERE appointment_id = %s", (appointment_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Appointment deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api')
def api_root():
    return jsonify({"message": "Hospital HMS API is running!"})

if __name__ == '__main__':
    app.run(port=5333, debug=True)
