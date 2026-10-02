import os
import io
import json
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_socketio import SocketIO, emit, join_room, leave_room
import pandas as pd

app = Flask(__name__, template_folder='templates')
app.secret_key = 'visit_automator_secret_key_12345'

socketio = SocketIO(app, cors_allowed_origins='*')

DB_FILE = 'database.db'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()

  c.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, visit_date TEXT, team_id TEXT, name TEXT, address TEXT, source TEXT, duration_mins INTEGER, latitude REAL, longitude REAL, confirmed INTEGER DEFAULT 1, is_completed INTEGER DEFAULT 0)''')

  c.execute('''CREATE TABLE IF NOT EXISTS student_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, visit_date TEXT, visits_json TEXT)''')

  c.execute('''CREATE TABLE IF NOT EXISTS visit_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, visit_date TEXT, team_id TEXT, student_id TEXT, student_name TEXT, company_id TEXT, company_name TEXT, person_met TEXT, contact_no TEXT, hr_email TEXT, visit_status TEXT, overall_conversation TEXT, feedback_notes TEXT, image_path TEXT)''')

  c.execute('''CREATE TABLE IF NOT EXISTS trip_status (
            status_key TEXT PRIMARY KEY, is_started INTEGER)''')
            
  c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, team_id TEXT, sender TEXT, role TEXT, message TEXT, timestamp TEXT)''')

  c.execute('SELECT COUNT(*) FROM companies')
  if c.fetchone()[0] == 0:
    c.execute('''INSERT INTO companies (visit_date, team_id, name, address, source, duration_mins, latitude, longitude, confirmed) VALUES 
            ('2026-10-12', 'TEAM-1', 'Tokai Imperial Rubber India Pvt. Ltd.', '45 Milestone, VPO Prithla, Palwal - 121102', 'Outreach', 10, 28.2231, 77.3188, 1),
            ('2026-10-12', 'TEAM-1', 'Maruti Suzuki (Manesar plant)', 'Plot No. 1, Phase 3A, IMT Manesar, Gurgaon 122051', 'Referral', 15, 28.3517, 76.9428, 1),
            ('2026-10-13', 'TEAM-1', 'Hero MotoCorp Ltd.', '34th Milestone, Delhi-Jaipur Highway, Gurgaon', 'Outreach', 15, 28.3812, 77.0125, 1),
            ('2026-10-14', 'TEAM-1', 'Honda Motorcycle & Scooter', 'Plot No. 1, Sector 3, IMT Manesar', 'Outreach', 12, 28.3620, 76.9350, 1),
            ('2026-10-15', 'TEAM-1', 'Escorts Kubota Ltd.', 'Sector 13, Faridabad, Haryana', 'Referral', 10, 28.4089, 77.3178, 1),
            ('2026-10-16', 'TEAM-1', 'Lohia Machines Ltd.', 'Mathura Road, Palwal', 'Outreach', 10, 28.1487, 77.3320, 1),
            ('2026-10-17', 'TEAM-1', 'Jindal Steels', 'Industrial Area, Ballabhgarh', 'Outreach', 15, 28.3375, 77.3210, 1),

            ('2026-10-12', 'TEAM-2', 'Nagarro Gurgaon', 'Plot No. 13, Electronic City, Sector 18, Gurugram', 'Outreach', 10, 28.4595, 77.0266, 1),
            ('2026-10-13', 'TEAM-2', 'TCS Gurgaon', 'IT Park, Sector 48, Gurgaon', 'Referral', 15, 28.4231, 77.0450, 1),
            ('2026-10-14', 'TEAM-2', 'Wipro Technologies', 'Udyog Vihar Phase V, Gurgaon', 'Outreach', 12, 28.4983, 77.0812, 1),
            ('2026-10-15', 'TEAM-2', 'Infosys Ltd.', 'Technology Park, Chandigarh Road, Gurgaon', 'Outreach', 10, 28.4812, 77.0721, 1),
            ('2026-10-16', 'TEAM-2', 'HCL Technologies', 'Sector 60, Golf Course Ext Rd, Gurgaon', 'Referral', 15, 28.4110, 77.0650, 1),
            ('2026-10-17', 'TEAM-2', 'Tech Mahindra', 'Sector 32, Institutional Area, Gurgaon', 'Outreach', 10, 28.4412, 77.0512, 1),

            ('2026-10-12', 'TEAM-3', 'Samsung Electronics Noida', 'B-1, Sector 81, Phase II, Noida', 'Outreach', 10, 28.5355, 77.3910, 1),
            ('2026-10-13', 'TEAM-3', 'Adobe Systems Noida', 'Plot 46, Sector 132, Noida', 'Referral', 15, 28.5021, 77.3750, 1),
            ('2026-10-14', 'TEAM-3', 'Paytm Headquarters', 'Sector 5, Noida, Uttar Pradesh', 'Outreach', 12, 28.5821, 77.3150, 1),
            ('2026-10-15', 'TEAM-3', 'HCL Infosystems', 'Sector 3, Noida', 'Outreach', 10, 28.5700, 77.3200, 1),
            ('2026-10-16', 'TEAM-3', 'Birlasoft', 'Sector 63, Noida', 'Referral', 15, 28.6120, 77.3780, 1),
            ('2026-10-17', 'TEAM-3', 'Nucleus Software', 'Sector 62, Noida', 'Outreach', 10, 28.6210, 77.3650, 1),

            ('2026-10-12', 'TEAM-4', 'Jindal Stainless Ltd. Hisar', 'OP Jindal Marg, Hisar, Haryana 125005', 'Outreach', 10, 29.1492, 75.7217, 1),
            ('2026-10-13', 'TEAM-4', 'Auto Pins India Hisar', 'Industrial Area, Hisar', 'Referral', 15, 29.1550, 75.7100, 1),
            ('2026-10-14', 'TEAM-4', 'Haryana Agro Industries', 'Civil Lines, Hisar', 'Outreach', 12, 29.1600, 75.7000, 1),
            ('2026-10-15', 'TEAM-4', 'Hisar Textile Mills', 'Delhi Road, Hisar', 'Outreach', 10, 29.1400, 75.7350, 1),
            ('2026-10-16', 'TEAM-4', 'Pawan Steel Works', 'Industrial Estate, Hisar', 'Referral', 15, 29.1450, 75.7250, 1),
            ('2026-10-17', 'TEAM-4', 'Agroha Agro Foods', 'Hisar-Barwala Road, Hisar', 'Outreach', 10, 29.1750, 75.7500, 1)''')

  conn.commit()
  conn.close()

init_db()

STUDENT_USERS = {
    'STU-1001': {'password': 'password123', 'team_id': 'TEAM-1', 'name': 'Roushan Kumar (Team Lead)'},
    'STU-1002': {'password': 'password123', 'team_id': 'TEAM-1', 'name': 'Nitish'},
    'STU-1003': {'password': 'password123', 'team_id': 'TEAM-1', 'name': 'Suryansh'},
    'STU-1004': {'password': 'password123', 'team_id': 'TEAM-1', 'name': 'Sakshi'},
    
    'STU-1005': {'password': 'password123', 'team_id': 'TEAM-2', 'name': 'Neha'},
    'STU-1006': {'password': 'password123', 'team_id': 'TEAM-2', 'name': 'Mamta'},
    'STU-1007': {'password': 'password123', 'team_id': 'TEAM-2', 'name': 'Amit Sharma'},
    'STU-1008': {'password': 'password123', 'team_id': 'TEAM-2', 'name': 'Rahul Verma'},

    'STU-1009': {'password': 'password123', 'team_id': 'TEAM-3', 'name': 'Vikas Singh'},
    'STU-1010': {'password': 'password123', 'team_id': 'TEAM-3', 'name': 'Pooja Sharma'},
    'STU-1011': {'password': 'password123', 'team_id': 'TEAM-3', 'name': 'Ankit Kumar'},
    'STU-1012': {'password': 'password123', 'team_id': 'TEAM-3', 'name': 'Ritu Rani'},

    'STU-1013': {'password': 'password123', 'team_id': 'TEAM-4', 'name': 'Deepak Kumar'},
    'STU-1014': {'password': 'password123', 'team_id': 'TEAM-4', 'name': 'Kajal Verma'},
    'STU-1015': {'password': 'password123', 'team_id': 'TEAM-4', 'name': 'Rohitashwa'},
    'STU-1016': {'password': 'password123', 'team_id': 'TEAM-4', 'name': 'Priyanka'}
}

CITY_COORDINATES = {
    'palwal': (28.1487, 77.3320), 'prithla': (28.2231, 77.3188), 'manesar': (28.3517, 76.9428),
    'gurgaon': (28.4595, 77.0266), 'noida': (28.5355, 77.3910), 'hisar': (29.1492, 75.7217),
    'delhi': (28.6139, 77.2090), 'faridabad': (28.4089, 77.3178)
}

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    team_id = str(request.form.get('team_id', '')).strip().upper()
    student_id = str(request.form.get('student_id', '')).strip().upper()
    password = str(request.form.get('password', '')).strip()

    if student_id in STUDENT_USERS:
      user = STUDENT_USERS[student_id]
      if user['password'] == password and user['team_id'] == team_id:
        session['logged_in'] = True
        session['student_id'] = student_id
        session['student_name'] = user['name']
        session['team_id'] = team_id
        return redirect('/student')
    return render_template('login.html', error='Galat Credentials! Dobara try karein.')
  return render_template('login.html')

@app.route('/student')
def student():
  if not session.get('logged_in'): return redirect('/login')
  return render_template('student.html', student_id=session.get('student_id'), student_name=session.get('student_name'), team_id=session.get('team_id'))

@app.route('/logout')
def logout():
  session.clear()
  return redirect('/login')

@app.route('/api/students-list', methods=['GET'])
def get_students_list():
  return jsonify({'students': STUDENT_USERS}), 200

@app.route('/api/add-manual-company', methods=['POST'])
def add_manual_company():
  req = request.get_json(force=True)
  name = req.get('name')
  address = req.get('address')
  lat = req.get('latitude')
  lng = req.get('longitude')
  visit_date = req.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
  team_id = req.get('team_id', 'TEAM-1').upper()

  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('''INSERT INTO companies (visit_date, team_id, name, address, source, duration_mins, latitude, longitude, confirmed) 
               VALUES (?, ?, ?, ?, 'Manual', 10, ?, ?, 1)''', (visit_date, team_id, name, address, lat, lng))
  conn.commit()
  conn.close()
  return jsonify({'status': 'success', 'message': 'Company added successfully!'}), 200

@app.route('/api/team-companies/<visit_date>/<team_id>', methods=['GET'])
def get_team_companies(visit_date, team_id):
  clean_date = visit_date.replace('/', '-')
  if len(clean_date.split('-')[0]) == 2:
    parts = clean_date.split('-')
    clean_date = f'{parts[2]}-{parts[1]}-{parts[0]}'
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('SELECT id, name, address, source, duration_mins, latitude, longitude, confirmed, is_completed FROM companies WHERE (visit_date = ? OR visit_date = ?) AND UPPER(team_id) = ?', (visit_date, clean_date, team_id.upper()))
  rows = c.fetchall()
  conn.close()
  companies = [{'id': r[0], 'name': r[1], 'address': r[2], 'source': r[3], 'durationMins': r[4], 'latitude': r[5], 'longitude': r[6], 'confirmed': bool(r[7]), 'isCompleted': bool(r[8]), 'visitDate': visit_date} for r in rows]
  return jsonify({'visit_date': visit_date, 'team_id': team_id, 'data': companies}), 200

@app.route('/api/update-company-selection', methods=['POST'])
def update_company_selection():
  req_data = request.get_json(force=True)
  comp_id = req_data.get('company_id')
  confirmed = 1 if req_data.get('confirmed') else 0

  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('UPDATE companies SET confirmed = ? WHERE id = ?', (confirmed, comp_id))
  
  # Agar admin ne uncheck kiya hai, toh sabhi student assignments se us company ko hata do
  if confirmed == 0:
    c.execute('SELECT id, student_id, visits_json FROM student_assignments')
    assignments = c.fetchall()
    for assign_id, student_id, visits_str in assignments:
      try:
        visits = json.loads(visits_str)
        new_visits = [v for v in visits if str(v.get('id')) != str(comp_id)]
        if len(new_visits) != len(visits):
          c.execute('UPDATE student_assignments SET visits_json = ? WHERE id = ?', (json.dumps(new_visits), assign_id))
          socketio.emit('student_route_updated', {'student_id': student_id})
      except Exception:
        pass

  conn.commit()
  conn.close()
  return jsonify({'status': 'success'}), 200

@app.route('/api/assign-to-student', methods=['POST'])
def assign_to_student():
  req_data = request.get_json(force=True)
  student_id = req_data.get('student_id')
  visit_date = req_data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
  selected_visits = req_data.get('selected_companies', [])
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('DELETE FROM student_assignments WHERE student_id = ? AND visit_date = ?', (student_id, visit_date))
  c.execute('INSERT INTO student_assignments (student_id, visit_date, visits_json) VALUES (?, ?, ?)', (student_id, visit_date, json.dumps(selected_visits)))
  conn.commit()
  conn.close()
  socketio.emit('student_route_updated', {'student_id': student_id, 'visit_date': visit_date, 'visits': selected_visits})
  return jsonify({'status': 'success', 'message': f'Assigned {len(selected_visits)} visits permanently!'}), 200

@app.route('/api/student-visits', methods=['GET'])
def get_student_visits():
  student_id = session.get('student_id')
  team_id = session.get('team_id')
  visit_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('SELECT visits_json FROM student_assignments WHERE student_id = ? AND visit_date = ?', (student_id, visit_date))
  row = c.fetchone()
  visits = json.loads(row[0]) if row else []
  c.execute('SELECT is_started FROM trip_status WHERE status_key = ?', (f'{visit_date}_{team_id}',))
  trip_row = c.fetchone()
  conn.close()
  return jsonify({'student_id': student_id, 'team_id': team_id, 'visit_date': visit_date, 'trip_started': bool(trip_row[0]) if trip_row else False, 'visits': visits}), 200

@app.route('/api/submit-visit-report', methods=['POST'])
def submit_visit_report():
  student_id = session.get('student_id')
  student_name = session.get('student_name')
  team_id = session.get('team_id')
  visit_id = request.form.get('visit_id', '').strip()
  company_name = request.form.get('company_name', 'Unknown Company')
  visit_date = request.form.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
  person_met = request.form.get('person_met', '')
  contact_no = request.form.get('contact_no', '')
  hr_email = request.form.get('hr_email', '')
  visit_status = request.form.get('visit_status', 'Completed')
  overall_conversation = request.form.get('overall_conversation', '')
  feedback_notes = request.form.get('feedback_notes', '')
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  image_path = ""
  if 'visit_image' in request.files:
      file = request.files['visit_image']
      if file.filename != '':
          filename = f"{student_id}_{visit_id}_{file.filename}"
          file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
          file.save(file_path)
          image_path = f"/static/uploads/{filename}"

  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('''INSERT INTO visit_reports 
      (timestamp, visit_date, team_id, student_id, student_name, company_id, company_name, person_met, contact_no, hr_email, visit_status, overall_conversation, feedback_notes, image_path)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
      (timestamp, visit_date, team_id, student_id, student_name, visit_id, company_name, person_met, contact_no, hr_email, visit_status, overall_conversation, feedback_notes, image_path))

  c.execute('SELECT visits_json FROM student_assignments WHERE student_id = ? AND visit_date = ?', (student_id, visit_date))
  row = c.fetchone()
  if row:
    visits = json.loads(row[0])
    for v in visits:
      if str(v.get('id')) == str(visit_id):
        v['isCompleted'] = True
        v['is_completed'] = True
        break
    c.execute('UPDATE student_assignments SET visits_json = ? WHERE student_id = ? AND visit_date = ?', (json.dumps(visits), student_id, visit_date))
  conn.commit()
  conn.close()
  socketio.emit('new_feedback_submitted', {})
  return jsonify({'status': 'success'}), 200

@app.route('/api/delete-visit-report', methods=['POST'])
def delete_visit_report():
  req_data = request.get_json(force=True) or {}
  student_id = req_data.get('student_id') or session.get('student_id')
  company_name = req_data.get('company_name')
  visit_id = req_data.get('visit_id')
  visit_date = req_data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  if visit_id: c.execute('DELETE FROM visit_reports WHERE company_id = ? AND visit_date = ?', (str(visit_id), visit_date))
  elif company_name: c.execute('DELETE FROM visit_reports WHERE company_name = ? AND visit_date = ?', (company_name, visit_date))
  if student_id:
    c.execute('SELECT visits_json FROM student_assignments WHERE student_id = ? AND visit_date = ?', (student_id, visit_date))
    row = c.fetchone()
    if row:
      visits = json.loads(row[0])
      for v in visits:
        if (visit_id and str(v.get('id')) == str(visit_id)) or (company_name and v.get('name') == company_name):
          v['isCompleted'] = False
          v['is_completed'] = False
          break
      c.execute('UPDATE student_assignments SET visits_json = ? WHERE student_id = ? AND visit_date = ?', (json.dumps(visits), student_id, visit_date))
  conn.commit()
  conn.close()
  socketio.emit('student_route_updated', {'student_id': student_id, 'visit_date': visit_date})
  socketio.emit('new_feedback_submitted', {})
  return jsonify({'status': 'success'}), 200

@app.route('/api/get-submitted-reports', methods=['GET'])
def get_submitted_reports():
  team_id = request.args.get('team_id', '').strip().upper()
  visit_date = request.args.get('visit_date', '').strip()
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  query = 'SELECT timestamp, student_id, student_name, company_name, person_met, contact_no, hr_email, visit_status, overall_conversation, feedback_notes, image_path FROM visit_reports WHERE 1=1'
  params = []
  if team_id: query += ' AND team_id = ?'; params.append(team_id)
  if visit_date: query += ' AND visit_date = ?'; params.append(visit_date)
  query += ' ORDER BY id DESC'
  c.execute(query, params)
  rows = c.fetchall()
  conn.close()
  reports = [{'timestamp': r[0], 'student_id': r[1], 'student_name': r[2], 'company_name': r[3], 'person_met': r[4], 'contact_no': r[5], 'hr_email': r[6], 'visit_status': r[7], 'overall_conversation': r[8], 'feedback_notes': r[9], 'image_path': r[10]} for r in rows]
  return jsonify({'status': 'success', 'reports': reports}), 200

@app.route('/api/toggle-trip', methods=['POST'])
def toggle_trip():
  req_data = request.get_json(force=True) or {}
  team_id = req_data.get('team_id', 'TEAM-1')
  visit_date = req_data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
  status_key = f'{visit_date}_{team_id}'
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('SELECT is_started FROM trip_status WHERE status_key = ?', (status_key,))
  row = c.fetchone()
  new_status = not bool(row[0]) if row else True
  c.execute('INSERT OR REPLACE INTO trip_status (status_key, is_started) VALUES (?, ?)', (status_key, int(new_status)))
  conn.commit()
  conn.close()
  socketio.emit('trip_status_changed', {'team_id': team_id, 'visit_date': visit_date, 'trip_started': new_status})
  return jsonify({'status': 'success', 'trip_started': new_status}), 200

@app.route('/api/get-chat-history/<team_id>', methods=['GET'])
def get_chat_history(team_id):
  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('SELECT sender, role, message FROM chat_messages WHERE team_id = ? ORDER BY id ASC', (team_id.upper(),))
  rows = c.fetchall()
  conn.close()
  messages = [{'sender': r[0], 'role': r[1], 'message': r[2]} for r in rows]
  return jsonify({'messages': messages}), 200

@socketio.on('update_student_location')
def handle_student_location(data): emit('student_location_response', data, broadcast=True)

@socketio.on('join_team_room')
def handle_join_team_room(data): join_room(f"room_{data.get('team_id', 'TEAM-1')}")

@socketio.on('send_message')
def handle_message(data):
  team_id = data.get('team_id', 'TEAM-1').upper()
  sender = data.get('sender')
  role = data.get('role')
  message = data.get('message')
  timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  conn = sqlite3.connect(DB_FILE)
  c = conn.cursor()
  c.execute('INSERT INTO chat_messages (team_id, sender, role, message, timestamp) VALUES (?, ?, ?, ?, ?)', (team_id, sender, role, message, timestamp))
  conn.commit()
  conn.close()

  emit('chat_message', data, to=f"room_{team_id}")

if __name__ == '__main__':
  socketio.run(app, debug=True, host='0.0.0.0', port=5000)