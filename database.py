import sqlite3
from flask import Flask#, g

# def get_db():
#     db = getattr(g, '_database', None)
#     if db is None:
#         db = g._database = sqlite3.connect("History.db")
#     return db

def get_db_connection(database):
    if database == 1:
        conn = sqlite3.connect('Details.db')
        conn.row_factory = sqlite3.Row
        return conn
    elif database == 2:
        conn = sqlite3.connect('History.db')
        conn.row_factory = sqlite3.Row
        return conn

def initialize_database(sender, database, **extra):
    if database == 1:
        conn = get_db_connection(1)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS details (
                id integer PRIMARY KEY ,
                username TEXT UNIQUE,
                name TEXT,
                phone INTEGER,
                age INTEGER,
                gender TEXT,
                email TEXT,
                password TEXT,
                OTP TEXT,
                image BLOB,
                remarks TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    elif database == 2:
        conn = get_db_connection(2)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Pregnancy (
                PatientID INTEGER,
                PregnancyID INTEGER PRIMARY KEY ,
                YearOfPregnancy INTEGER,
                DeliveryType TEXT CHECK (DeliveryType IN ('normal', 'c section', 'testube', 'not yet delivered')),
                Complicationbefore TEXT,
                Complicationafter TEXT,
                ChildGender TEXT,
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Surgery (
                SurgeryID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                SurgeryType TEXT,
                Date DATE,
                Outcome TEXT,
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Vaccination (
                VaccinationID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                VaccinationName TEXT,
                DateOfVaccination DATE,
                Dosage TEXT,
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DailyInputs (
                InputID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                Date DATE,
                BfPreTime TIME,
                BfSugarLevelPre REAL,
                BfPostTime TIME,
                BfSugarLevelPost REAL,
                LunchPreTime TIME,
                LunchSugarLevelPre REAL,
                LunchPostTime TIME,
                LunchSugarLevelPost REAL,
                DinnerPreTime TIME,
                DinnerSugarLevelPre REAL,
                DinnerPostTime TIME,
                DinnerSugarLevelPost REAL,
                BPTime TIME,
                BP INTEGER,
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Medicine (
                MedicineID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                MedicineName TEXT,
                Dosage TEXT,
                Quantity INTEGER,
                DurationDays INTEGER,
                DailyTime TEXT CHECK (DailyTime IN ('before meal', 'after meal')),
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Patient (
                PatientID INTEGER PRIMARY KEY ,
                Name TEXT,
                DOB DATE,
                Gender TEXT,
                Age INTEGER,
                BloodGroup TEXT,
                Photo BLOB,
                height decimal,
                weight decimal,
                bmi decimal,
                Contact TEXT,
                EmergencyContact TEXT,
                Address TEXT,
                MedicalProblems BOOLEAN,
                Allergy BOOLEAN,
                Surgery BOOLEAN,
                Pregnancy BOOLEAN,
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Allergies (
                AllergyID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                AllergyName TEXT,
                AllergyArea TEXT,
                AllergyEffect TEXT,
                AllergyType TEXT CHECK (AllergyType IN ('food', 'drug')),
                image BLOB,
                remarks TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS MedicalProblems (
                DiseaseID INTEGER PRIMARY KEY ,
                PatientID INTEGER,
                DiseaseName TEXT,
                Status TEXT,
                Date DATE,
                image BLOB,
                remarks TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
