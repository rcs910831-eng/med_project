#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize database with real schema and sample data"""

import sqlite3
from datetime import datetime, timedelta
import random
import shutil

# Backup existing DB
shutil.copy('pharma_mobile.db', 'pharma_mobile.db.backup_old')
print("[OK] Backup created\n")

# Create new database
conn = sqlite3.connect('pharma_mobile.db')
c = conn.cursor()

# Drop old tables
c.execute("DROP TABLE IF EXISTS prescriptions")
c.execute("DROP TABLE IF EXISTS patients")
c.execute("DROP TABLE IF EXISTS healthcare_providers")

print("[1/4] Creating tables...")

# Create tables
c.execute('''
CREATE TABLE healthcare_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    license_number TEXT NOT NULL,
    specialty TEXT,
    hospital TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    phone TEXT,
    address TEXT,
    medical_history TEXT,
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE prescriptions (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    medication TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    duration TEXT,
    quantity INTEGER,
    diagnosis TEXT,
    notes TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id),
    FOREIGN KEY(doctor_id) REFERENCES healthcare_providers(id)
)
''')

conn.commit()
print("[OK] Tables created\n")

print("[2/4] Inserting providers...")

doctors = [
    ('DOC001', '김의사', 'LIC-2020-001', '내과', '서울의료원', 'kim@hospital.kr', '02-1234-1111'),
    ('DOC002', '이약사', 'LIC-2019-002', '약학', '강남약국', 'lee@pharmacy.kr', '02-2222-2222'),
    ('DOC003', '박의사', 'LIC-2021-003', '심장내과', '삼성병원', 'park@samsung.kr', '02-3333-3333'),
]

for doc in doctors:
    c.execute('''INSERT INTO healthcare_providers
                 (id, name, license_number, specialty, hospital, email, phone)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', doc)

conn.commit()
print(f"[OK] {len(doctors)} providers inserted\n")

print("[3/4] Inserting patients...")

patients_data = [
    ('PT001', '김철수', '1956-03-15', 'M', '010-1111-1111', '서울시 강남구', '고혈압, 당뇨병', '페니실린'),
    ('PT002', '이영희', '1965-07-22', 'F', '010-2222-2222', '서울시 서초구', '갑상선질환', '없음'),
    ('PT003', '박준호', '1978-11-08', 'M', '010-3333-3333', '서울시 강동구', '천식', '아스피린'),
    ('PT004', '최민지', '1990-01-30', 'F', '010-4444-4444', '서울시 마포구', '없음', '없음'),
    ('PT005', '정수진', '1962-05-12', 'F', '010-5555-5555', '서울시 중구', '고혈압', '없음'),
    ('PT006', '이동욱', '1975-09-18', 'M', '010-6666-6666', '서울시 종로구', '당뇨병', '없음'),
    ('PT007', '강미경', '1988-04-25', 'F', '010-7777-7777', '서울시 영등포구', '갑상선', '요오드'),
    ('PT008', '조성민', '1970-12-03', 'M', '010-8888-8888', '서울시 은평구', '우울증', '없음'),
    ('PT009', '유현주', '1985-06-17', 'F', '010-9999-9999', '서울시 동대문구', '편두통', '없음'),
    ('PT010', '황진욱', '1972-10-29', 'M', '010-0000-0000', '서울시 성동구', '고콜레스테롤', '없음'),
]

for patient in patients_data:
    c.execute('''INSERT INTO patients
                 (id, name, date_of_birth, gender, phone, address, medical_history, allergies)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', patient)

conn.commit()
print(f"[OK] {len(patients_data)} patients inserted\n")

print("[4/4] Inserting prescriptions...")

medications = [
    ('노바스크정', '5mg', '1회 1정', '아침'),
    ('글루코판정', '500mg', '2회 1정', '아침/저녁'),
    ('신지로이정', '100mg', '1회 1정', '저녁'),
    ('종로정', '250mg', '1회 2정', '아침'),
    ('아토르바정', '20mg', '1회 1정', '저녁'),
    ('메토프롤정', '50mg', '1회 1정', '아침'),
    ('오메프라졸', '20mg', '1회 1정', '아침'),
    ('프로칼정', '150mg', '1회 1정', '저녁'),
]

diagnoses = ['고혈압', '당뇨병', '갑상선질환', '천식', '고지혈증', '위염', '불면증', '편두통']

prescription_id = 1
for _ in range(128):
    patient_id = f"PT{random.randint(1, 10):03d}"
    doctor_id = random.choice(['DOC001', 'DOC002', 'DOC003'])
    med_name, dosage, freq, timing = random.choice(medications)
    diagnosis = random.choice(diagnoses)

    days_ago = random.randint(1, 180)
    created_date = (datetime.now() - timedelta(days=days_ago)).isoformat()

    c.execute('''INSERT INTO prescriptions
                 (id, patient_id, doctor_id, medication, dosage, frequency, duration, quantity, diagnosis, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (f'RX{prescription_id:05d}', patient_id, doctor_id, med_name, dosage, freq, '30일',
              random.randint(10, 100), diagnosis, 'active', created_date))

    prescription_id += 1

conn.commit()

# Verify
c.execute("SELECT COUNT(*) FROM patients")
patient_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM prescriptions")
prescription_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM healthcare_providers")
provider_count = c.fetchone()[0]

print(f"[OK] 128 prescriptions inserted\n")

print("="*60)
print("DATABASE READY")
print("="*60)
print(f"Patients:        {patient_count}")
print(f"Prescriptions:   {prescription_count}")
print(f"Providers:       {provider_count}")
print("="*60 + "\n")

conn.close()
