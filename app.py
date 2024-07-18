import socket
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
import qrcode
import os
import io
from PIL import Image
import numpy as np
import cv2
from database import get_db_connection, initialize_database
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
import random
import smtplib
import webbrowser as w
from twilio.rest import Client
import base64

app = Flask(__name__)
app.secret_key = "ksdjaflkjhsdflkjahsdflkjasdflkjhsaflkjasdflkkjajsdfkjj"

hosts = "usim.pythonanywhere.com"
# global variables are here bros
qrdata = ""
otp = "999"
account_sid = 'ACf43333dc043778e2a278037b0536ca94'
auth_token = 'd330934aa3f219977037571fd97e7a23'
client = Client(account_sid, auth_token)
num = "+601164341687"

# all functions are declared here bros
def get_local_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def generate_key_value_qrcode(key, value, filename="static/qrcode.png"):
    base_url = f"https://{hosts}:5000/profile"
    # base_url = f"https://{hosts}/profile"
    data = f"{base_url}?{key}={value}"
    global qrdata
    qrdata = data
    qr = qrcode.QRCode(version=2, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

def send_email(to_email, OTP):
    from_email = "clinicalsystem2@gmail.com"
    from_password = "eiig ydgo nqkf aown"
    subject = "Your OTP"
    body = f"Your OTP is: {OTP}"

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_random_password(length=4):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def save_file(file):
    if file:
        file_path = os.path.join('static/uploads', file.filename)
        file.save(file_path)
        with open(file_path, 'rb') as f:
            image_data = f.read()
        return image_data
    return None

@app.route('/dashboard')
def dashboard():
    patient_id = request.args.get('patient_id')
    db = get_db_connection(2)
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Patient WHERE PatientID=?', patient_id)
    patient_details = cursor.fetchone()
    cursor.execute('SELECT Date, BP FROM DailyInputs WHERE PatientID = ?', (patient_details['PatientID'],))
    bp_levels = cursor.fetchall()
    cursor.execute('SELECT Date, DinnerSugarLevelPost FROM DailyInputs WHERE PatientID = ?', (patient_details['PatientID'],))
    sugar_levels = cursor.fetchall()
    bp_image = create_graph(bp_levels, 'BP Levels', 'Date', 'BP Level')
    sugar_image = create_graph(sugar_levels, 'Sugar Levels', 'Date', 'Sugar Level')

    return render_template('dashboard.html', patient_details=patient_details, bp_image=bp_image, sugar_image=sugar_image)

@app.route('/fetch/<table_name>', methods=['GET'])
def fetch_table_data(table_name):
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    cursor.close()
    conn.close()
    return jsonify({"columns": columns, "rows": [dict(row) for row in rows]})

def create_graph(data, title, xlabel, ylabel):
    dates = [row[0] for row in data]
    values = [row[1] for row in data]

    plt.figure()
    plt.plot(dates, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return 'data:image/png;base64,{}'.format(plot_url)

# Routes
@app.route('/edit_record/<table>/<record_id>', methods=['GET', 'POST'])
def edit_record(table, record_id):
    conn = get_db_connection(2)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Assuming all fields are submitted via a form
        form_data = request.form.to_dict()
        columns = ', '.join([f"{key}=?" for key in form_data.keys()])
        values = list(form_data.values())
        values.append(record_id)
        query = f"UPDATE {table} SET {columns} WHERE id=?"
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('show_history', patient_id=form_data.get('PatientID')))
    
    # GET method - fetch the record to be edited
    cursor.execute(f"SELECT * FROM {table} WHERE PatientID=?", (record_id,))
    record = cursor.fetchone()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [column['name'] for column in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    return render_template('edit_record.html', table=table, record=record, columns=columns)
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/scanqr')
def scanqr():
    return render_template('scanqr.html')
@app.route('/upload_qr', methods=['POST'])
def upload_qr():
    file = request.files.get('file')
    image_data_url = request.form.get('image')

    if file:
        try:
            img = Image.open(file)
        except Exception as e:
            return jsonify({'error': str(e)})
    elif image_data_url:
        try:
            img_data = base64.b64decode(image_data_url.split(',')[1])
            img = Image.open(io.BytesIO(img_data))
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'error': 'No file or image data provided'})

    try:
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        if bbox is not None and data:
            return jsonify({'data': data})
        else:
            return jsonify({'error': 'No QR code found'})
    except Exception as e:
        return jsonify({'error': str(e)})
@app.route('/upload_ocr', methods=['POST'])
def upload_ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        try:
            img = Image.open(file)
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if bbox is not None and data:
                return jsonify({'data': data})
            else:
                return jsonify({'error': 'No QR code found'})
        except Exception as e:
            return jsonify({'error': str(e)})
    return jsonify({'error': 'File not processed'})

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        return redirect('home')
    return render_template('contact.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form['email']
    global otp
    otp = generate_random_password()
    send_email(email, otp)
    return otp, 200

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_id = request.form['patient_id']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        otp_entered = request.form['otp']
        conn = get_db_connection(1)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM DETAILS")
        idss = cursor.fetchall()
        ids = []
        users = []
        for i in idss:
            l1 = list(i)[0]
            l2 = list(i)[1]
            ids.append(l1)
            users.append(l2)

        if user_id in ids:
            flash('Invalid ID in use')
            return render_template('signup.html', patient_id=user_id)
        if username in users:
            flash('Invalid username in use')
            return render_template('signup.html', patient_id=user_id)
        if otp == otp_entered:
            if phone:
                cursor.execute('INSERT INTO details(id, username, phone, password, OTP) VALUES (?,?,?,?,?)', (user_id, username, phone, password, otp_entered))
            else:
                cursor.execute('INSERT INTO details(id, username, email, password, OTP) VALUES (?,?,?,?,?)', (user_id, username, email, password, otp_entered))
            conn.commit()
            conn.close()
            flash('User registered successfully.')
            generate_key_value_qrcode("patient_id", user_id)
            return render_template('qr_display.html', patient_id=user_id, link=qrdata)
        else:
            flash('Invalid OTP. Please try again.')
            return redirect(url_for('signup'))
    return render_template("signup.html")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection(1)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM DETAILS WHERE email=?", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            user_id = user['id']
            # Generate a QR code pointing to the settings page for this user
            generate_key_value_qrcode("patient_id", user_id, filename="static/settings_qr.png")
            # URL to settings page
            settings_url = f"http://{hosts}:5000/settings?patient_id={user_id}"
            # Send email with link to settings page
            send_email(email, f"Click this link to reset your password: {settings_url}")
            flash('An email has been sent to reset your password.')
        else:
            flash('Email not found. Please try again.')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    patient_id = ""
    username = ""
    if request.method == 'POST':
        userid = request.form['patient_id']
        if userid.isdigit():
            patient_id = userid
        else:
            username = userid
        pwd = request.form['password']
        conn = get_db_connection(1)
        cursor = conn.cursor()
        if patient_id != "":
            cursor.execute("SELECT * FROM DETAILS WHERE id=?", (patient_id,))
        else:
            cursor.execute("SELECT * FROM DETAILS WHERE username=?", (username,))
        patient = cursor.fetchone()
        cursor.close()
        conn.close()
        if patient:
            patient_id = patient["id"]
            db_pwd = patient["password"]
            if pwd == db_pwd:
                session['user_id'] = patient_id
                flash('Login successful!')
                generate_key_value_qrcode("patient_id", patient_id)
                return redirect(url_for('profile', patient_id=patient_id, link=qrdata))
            else:
                flash('Login failed. Please check your credentials and try again.')
                return render_template('login.html', patient_id=patient_id, second=True)
        else:
            return render_template('login.html', patient_id=patient_id)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/')
def home():
    logged_in = 'user_id' in session
    return render_template('home.html', logged_in=logged_in)

@app.route('/profile')
def profile():
    patient_id = request.args.get('patient_id')

    conn = get_db_connection(1)
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, gender FROM details WHERE id=?", (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()

    if patient:
        name, age, gender = patient['name'], patient['age'], patient['gender']
        return render_template('profile.html', patient_id=patient_id, name=name, age=age, gender=gender)
    else:
        return "Patient not found", 404

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    patient_id = request.args.get('patient_id')
    conn = get_db_connection(1)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM details WHERE id=?", (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()

    if patient:
        username, name, age, gender, email, password = patient['username'], patient['name'], patient['age'], patient['gender'], patient['email'], patient['password']
    return render_template("settings.html", patient_id=patient_id, username=username, name=name, age=age, gender=gender, email=email, password=password)

@app.route('/submit', methods=['POST'])
def submit():
    id = request.form['id']
    username = request.form['username']
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection(1)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM details WHERE id=?", (id,))
    patient = cursor.fetchone()
    if patient:
        if patient["password"] == password:
            pass
        cursor.execute("""UPDATE details SET name = ?, age = ?, gender = ?, email = ?, password = ? WHERE id = ?""",
                           (name, age, gender, email, password, id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('profile', patient_id=id))
    else:
        return redirect(url_for('settings.html', patient_id=id, username=username, name=name, age=age, gender=gender, email=email))

@app.route('/show_history')
def show_history():
    db = get_db_connection(2)
    patient_id = request.args.get('patient_id')
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    tables = [table[0] for table in tables]
    return render_template('jack.html', tables=tables, patient_id=patient_id)

@app.route('/table/<table_name>')
def show_table(table_name):
    conn = get_db_connection(2)
    patient_id = request.args.get('patient_id')
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name} WHERE PatientID=?"
    cursor.execute(query, (patient_id,))
    rows = cursor.fetchall()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column['name'] for column in cursor.fetchall()]

    data_rows = []
    images = []
    for row in rows:
        row_data = []
        for column in columns:
            cell = row[column]
            if isinstance(cell, bytes):
                encoded_image = base64.b64encode(cell).decode('utf-8')
                images.append(encoded_image)
                row_data.append(encoded_image)
            else:
                row_data.append(cell)
        data_rows.append(row_data)

    response_data = {
        "columns": columns,
        "rows": data_rows,
        "images": images
    }

    return jsonify(response_data)

@app.route('/add_all')
def add_all():
    patient_id = request.args.get('patient_id')
    return render_template('add_all.html', patient_id=patient_id)

@app.route('/submit_patient', methods=['POST'])
def submit_patient():
    PatientID = request.form['PatientID']
    name = request.form['Name']
    DOB = request.form['DOB']
    gender = request.form['Gender']
    BloodGroup = request.form['BloodGroup']
    age = request.form['Age']
    weight = request.form['weight']
    height = request.form['height']
    bmi = request.form['bmi']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Patient (PatientID, Name, DOB, Gender, Age, BloodGroup, image, remarks, height, weight, bmi) VALUES (?,?,?,?, ?, ?, ?, ?, ?, ?, ?)',
                   (PatientID, name, DOB, gender, age, BloodGroup, image, remarks, height, weight, bmi))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_pregnancy', methods=['POST'])
def submit_pregnancy():
    PatientID = request.form['PatientID']
    YearOfPregnancy = request.form['YearOfPregnancy']
    DeliveryType = request.form['DeliveryType']
    Complicationbefore = request.form['Complicationbefore']
    Complicationafter = request.form['Complicationafter']
    ChildGender = request.form['ChildGender']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Pregnancy (PatientID, YearOfPregnancy, DeliveryType, Complicationbefore, Complicationafter, ChildGender, image, remarks) VALUES (?,?,?,?, ?, ?, ?, ?)',
                   (PatientID, YearOfPregnancy, DeliveryType, Complicationbefore, Complicationafter, ChildGender, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_surgery', methods=['POST'])
def submit_surgery():
    PatientID = request.form['PatientID']
    SurgeryType = request.form['SurgeryType']
    Date = request.form['Date']
    Outcome = request.form['Outcome']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Surgery (PatientID, SurgeryType, Date, Outcome, image, remarks) VALUES (?,?,?, ?, ?, ?)',
                   (PatientID, SurgeryType, Date, Outcome, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_vaccination', methods=['POST'])
def submit_vaccination():
    PatientID = request.form['PatientID']
    VaccinationName = request.form['VaccinationName']
    DateOfVaccination = request.form['DateOfVaccination']
    Dosage = request.form['Dosage']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Vaccination (PatientID, VaccinationName, DateOfVaccination, Dosage, image, remarks) VALUES (?,?,?, ?, ?, ?)',
                   (PatientID, VaccinationName, DateOfVaccination, Dosage, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_dailyinputs', methods=['POST'])
def submit_dailyinputs():
    PatientID = request.form['PatientID']
    Date = request.form['Date']
    BreakfastPreTime = request.form['BreakfastPreTime']
    BreakfastSugarLevelPre = request.form['BreakfastSugarLevelPre']
    BreakfastPostTime = request.form['BreakfastPostTime']
    BreakfastSugarLevelPost = request.form['BreakfastSugarLevelPost']
    LunchPreTime = request.form['LunchPreTime']
    LunchSugarLevelPre = request.form['LunchSugarLevelPre']
    LunchPostTime = request.form['LunchPostTime']
    LunchSugarLevelPost = request.form['LunchSugarLevelPost']
    DinnerPreTime = request.form['DinnerPreTime']
    DinnerSugarLevelPre = request.form['DinnerSugarLevelPre']
    DinnerPostTime = request.form['DinnerPostTime']
    DinnerSugarLevelPost = request.form['DinnerSugarLevelPost']
    BPTime = request.form['BPTime']
    BP = request.form['BP']
    image = request.files['file'].read() if 'file' in request.files else None  # Read the binary data of the uploaded file
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO DailyInputs (
            PatientID, Date, 
            bfPreTime, bfSugarLevelPre, 
            bfPostTime, bfSugarLevelPost, 
            LunchPreTime, LunchSugarLevelPre, 
            LunchPostTime, LunchSugarLevelPost, 
            DinnerPreTime, DinnerSugarLevelPre, 
            DinnerPostTime, DinnerSugarLevelPost, 
            BPTime, BP, image, remarks
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        PatientID, Date, 
        BreakfastPreTime, BreakfastSugarLevelPre, 
        BreakfastPostTime, BreakfastSugarLevelPost, 
        LunchPreTime, LunchSugarLevelPre, 
        LunchPostTime, LunchSugarLevelPost, 
        DinnerPreTime, DinnerSugarLevelPre, 
        DinnerPostTime, DinnerSugarLevelPost, 
        BPTime, BP, image, remarks
    ))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_medicine', methods=['POST'])
def submit_medicine():
    PatientID = request.form['PatientID']
    MedicineName = request.form['MedicineName']
    Dosage = request.form['Dosage']
    Quantity = request.form['Quantity']
    DurationDays = request.form['DurationDays']
    DailyTime = request.form['DailyTime']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Medicine (PatientID, MedicineName, Dosage, Quantity, DurationDays, DailyTime, image, remarks) VALUES (?,?,?, ?, ?, ?, ?, ?)',
                   (PatientID, MedicineName, Dosage, Quantity, DurationDays, DailyTime, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_allergies', methods=['POST'])
def submit_allergies():
    PatientID = request.form['PatientID']
    AllergyName = request.form['AllergyName']
    AllergyArea = request.form['AllergyArea']
    AllergyEffect = request.form['AllergyEffect']
    AllergyType = request.form['AllergyType']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Allergies (PatientID, AllergyName, AllergyArea, AllergyEffect, AllergyType, image, remarks) VALUES (?,?,?, ?, ?, ?, ?)',
                   (PatientID, AllergyName, AllergyArea, AllergyEffect, AllergyType, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))

@app.route('/submit_medicalproblems', methods=['POST'])
def submit_medicalproblems():
    PatientID = request.form['PatientID']
    DiseaseName = request.form['DiseaseName']
    Status = request.form['Status']
    Date = request.form['Date']
    image = save_file(request.files['file'])  # Save the uploaded file and read the binary data
    remarks = request.form['remarks']  # Get remarks from the form

    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO MedicalProblems (PatientID, DiseaseName, Status, Date, image, remarks) VALUES (?,?,?, ?, ?, ?)',
                   (PatientID, DiseaseName, Status, Date, image, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('profile', patient_id=PatientID))
@app.route('/pregnancy', methods=['GET'])
def fetch_pregnancy():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pregnancy")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('pregnancy.html', rows=rows)

@app.route('/surgery', methods=['GET'])
def fetch_surgery():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Surgery")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('surgery.html', rows=rows)

@app.route('/vaccination', methods=['GET'])
def fetch_vaccination():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vaccination")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('vaccination.html', rows=rows)

@app.route('/dailyinputs', methods=['GET'])
def fetch_dailyinputs():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM DailyInputs")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dailyinputs.html', rows=rows)

@app.route('/medicine', methods=['GET'])
def fetch_medicine():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Medicine")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('medicine.html', rows=rows)

@app.route('/patient', methods=['GET'])
def fetch_patient():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Patient")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('patient.html', rows=rows)

@app.route('/allergies', methods=['GET'])
def fetch_allergies():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Allergies")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('allergies.html', rows=rows)

@app.route('/medicalproblems', methods=['GET'])
def fetch_medicalproblems():
    conn = get_db_connection(2)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MedicalProblems")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('medicalproblems.html', rows=rows)
if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    hosts = get_local_ip()
    # hosts="usim.pythonanywhere.com"
    initialize_database(app, 1)
    initialize_database(app, 2)
    w.open(f"https://{hosts}:5000")
    app.run(host=hosts, port=5000 ,ssl_context=('cert.pem', 'key.pem'))
