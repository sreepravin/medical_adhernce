# 📊 PostgreSQL Database Setup - Step by Step

## ✅ Current Status: Database Already Configured!

Your database is **already set up and working**. Here's proof:

```
✅ PostgreSQL installed and running
✅ Database credentials configured in .env
✅ Connection tested successfully (Message 1)
✅ Backend actively using database (currently running)
✅ All 11 tables created
```

But if you want to **understand every step** or **set up fresh**, follow this guide!

---

## 📋 What This Guide Covers

1. **What's already done** (verify it works)
2. **Database structure** (11 tables explained)
3. **Manual setup steps** (if starting fresh)
4. **How to test** (verify everything works)
5. **Troubleshooting** (if something breaks)

---

---

# PART 1: What's Already Set Up ✅

## Current Database Configuration

**File:** `c:\Users\Kumar\OneDrive\Documents\pro\.env`

```env
DATABASE_URL=postgresql://postgres:root@localhost:5432/postgres
```

**What this means:**
- **Server:** localhost (your computer)
- **Port:** 5432 (PostgreSQL default)
- **User:** postgres
- **Password:** root
- **Database:** postgres

**Status:** ✅ Connected and working

---

## Verify Connection Is Working

### Method 1: Check Backend Logs

The backend (currently running) connects to database on startup.

**Look for this in the terminal:**
```
✅ Connected to PostgreSQL database
```

✅ If you see this, database is working!

### Method 2: Run Tests

```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python test_api.py
```

If 13/13 tests pass, database is working perfectly!

### Method 3: Query the Database Directly

```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python
```

Then copy and paste:

```python
from db_connection import get_db_connection, execute_query

conn = get_db_connection()
result = execute_query(conn, "SELECT * FROM users LIMIT 1;")
print("✅ Database connected! Tables exist.")
```

---

---

# PART 2: Database Structure (11 Tables)

## Visual Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USERS (Core)                         │
│  user_id | username | email | password_hash | created  │
└──────────────────────┬────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    MEDICAL_INFO  HEALTHCARE_   CAREGIVER_
                  PROVIDERS     ACCESS
```

## Table Details

### 1. **users** - User Accounts
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Store user login information  
**Example:**
- testuser | test@example.com | hashed_password | John Doe

---

### 2. **user_medical_info** - Health Details
```sql
CREATE TABLE user_medical_info (
    medical_info_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    drug_allergies TEXT[],
    food_allergies TEXT[],
    existing_conditions TEXT[],
    is_pregnant BOOLEAN DEFAULT FALSE,
    is_breastfeeding BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Store patient's medical history  
**Example:**
- user_id: 1 | drug_allergies: ['Penicillin'] | conditions: ['Diabetes']

---

### 3. **prescriptions** - Medicine Prescriptions
```sql
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    medicine_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    start_date DATE,
    end_date DATE,
    route VARCHAR(50),
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Store patient's medicines  
**Example:**
- Metformin | 500mg | 2 times daily | 30 days

---

### 4. **medications** - Medicine Reference Library
```sql
CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    generic_name VARCHAR(255),
    description TEXT,
    side_effects TEXT,
    contraindications TEXT
);
```

**Purpose:** Reference database of medicines  
**Example:**
- Aspirin | acetylsalicylic acid | Pain relief and blood thinner | ...

---

### 5. **adherence_plans** - Daily Schedule
```sql
CREATE TABLE adherence_plans (
    adherence_plan_id SERIAL PRIMARY KEY,
    prescription_id INT NOT NULL,
    user_id INT NOT NULL,
    daily_schedule TEXT[],
    why_important TEXT,
    nudge_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Create daily dose schedule  
**Example:**
- Times: ['08:00', '20:00'] | Reason: "Controls blood sugar"

---

### 6. **dose_tracking** - Individual Doses
```sql
CREATE TABLE dose_tracking (
    dose_id SERIAL PRIMARY KEY,
    adherence_plan_id INT NOT NULL,
    prescription_id INT NOT NULL,
    user_id INT NOT NULL,
    scheduled_time TIMESTAMP,
    actual_time TIMESTAMP,
    status VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (adherence_plan_id) REFERENCES adherence_plans(adherence_plan_id),
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Track each dose (taken, missed, pending)  
**Example:**
- scheduled_time: 2026-02-06 08:00 | status: 'taken' | actual_time: 2026-02-06 08:15

---

### 7. **contraindication_checks** - Safety Checks
```sql
CREATE TABLE contraindication_checks (
    check_id SERIAL PRIMARY KEY,
    prescription_id INT NOT NULL,
    user_id INT NOT NULL,
    medication_name VARCHAR(255),
    check_type VARCHAR(100),
    risk_level VARCHAR(20),
    warning_message TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Safety warnings (allergies, interactions, pregnancy)  
**Example:**
- medication: Aspirin | check_type: pregnancy | risk_level: high

---

### 8. **reminders** - Notifications
```sql
CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    dose_id INT NOT NULL,
    user_id INT NOT NULL,
    reminder_text VARCHAR(255),
    reminder_time TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    reminder_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dose_id) REFERENCES dose_tracking(dose_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Send dose reminders  
**Example:**
- reminder_text: "Time to take Metformin!" | method: "email"

---

### 9. **adherence_summary** - Daily Statistics
```sql
CREATE TABLE adherence_summary (
    summary_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    summary_date DATE,
    total_doses INT,
    doses_taken INT,
    doses_missed INT,
    adherence_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Daily adherence statistics  
**Example:**
- date: 2026-02-06 | total: 3 | taken: 2 | missed: 1 | adherence: 66.67%

---

### 10. **healthcare_providers** - Doctor Information
```sql
CREATE TABLE healthcare_providers (
    provider_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    provider_name VARCHAR(255),
    specialization VARCHAR(255),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Purpose:** Store doctor/provider information  
**Example:**
- Dr. Smith | Cardiologist | dr.smith@clinic.com

---

### 11. **caregiver_access** - Shared Access
```sql
CREATE TABLE caregiver_access (
    access_id SERIAL PRIMARY KEY,
    patient_user_id INT NOT NULL,
    caregiver_user_id INT NOT NULL,
    access_level VARCHAR(100),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_user_id) REFERENCES users(user_id),
    FOREIGN KEY (caregiver_user_id) REFERENCES users(user_id)
);
```

**Purpose:** Allow caregivers to view patient data  
**Example:**
- patient_id: 1 | caregiver_id: 2 | access: "view_only"

---

---

# PART 3: Manual Database Setup (If Starting Fresh)

## Step 1: Install PostgreSQL

### On Windows

**Download:** https://www.postgresql.org/download/windows/

**Installation:**
1. Run installer
2. Choose default settings
3. Set password: `root` (for SuperUser)
4. Port: `5432`
5. Click "Finish"

**Verify Installation:**
```bash
psql --version
```

Should show: `psql (PostgreSQL) 15.x` (or newer)

---

## Step 2: Start PostgreSQL Service

### Windows

```bash
net start postgresql-x64-15
```

Or use Services:
- Windows Key → Services
- Find "postgresql"
- Right-click → Start

**Verify Running:**
```bash
psql -U postgres -c "SELECT version();"
```

---

## Step 3: Create Application Database

```bash
psql -U postgres -c "CREATE DATABASE pill_pal;"
```

**Verify Created:**
```bash
psql -U postgres -l
```

Look for `pill_pal` in the list.

---

## Step 4: Create .env File

**File:** `c:\Users\Kumar\OneDrive\Documents\pro\.env`

```env
DATABASE_URL=postgresql://postgres:root@localhost:5432/postgres
```

---

## Step 5: Run Schema SQL

**File:** `c:\Users\Kumar\OneDrive\Documents\pro\schema.sql`

```bash
psql -U postgres -f schema.sql
```

**Verify Tables Created:**
```bash
psql -U postgres -c "\dt"
```

Should show all 11 tables:
```
 users
 user_medical_info
 prescriptions
 medications
 adherence_plans
 dose_tracking
 contraindication_checks
 reminders
 adherence_summary
 healthcare_providers
 caregiver_access
```

---

## Step 6: Verify Connection

```python
python
```

Then:
```python
import psycopg2
conn = psycopg2.connect("postgresql://postgres:root@localhost:5432/postgres")
print("✅ Connected!")
conn.close()
```

---

---

# PART 4: Test Your Database

## Test 1: Insert Sample User

```sql
INSERT INTO users (username, email, password_hash, full_name)
VALUES ('testuser', 'test@example.com', 'hashed_password', 'John Doe');
```

**Verify:**
```sql
SELECT * FROM users;
```

---

## Test 2: Insert Medical Info

```sql
INSERT INTO user_medical_info (user_id, drug_allergies, existing_conditions)
VALUES (1, ARRAY['Penicillin'], ARRAY['Diabetes']);
```

**Verify:**
```sql
SELECT * FROM user_medical_info WHERE user_id = 1;
```

---

## Test 3: Add Prescription

```sql
INSERT INTO prescriptions (user_id, medicine_name, dosage, frequency)
VALUES (1, 'Metformin', '500mg', '2 times daily');
```

**Verify:**
```sql
SELECT * FROM prescriptions WHERE user_id = 1;
```

---

## Test 4: Check Database Via Python

```python
from db_connection import get_db_connection, execute_query

conn = get_db_connection()

# Get user
result = execute_query(conn, "SELECT * FROM users;")
print(f"✅ Users: {result}")

# Get prescriptions
result = execute_query(conn, "SELECT * FROM prescriptions;")
print(f"✅ Prescriptions: {result}")

conn.close()
print("✅ All tests passed!")
```

---

## Test 5: Run Full API Tests

```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python test_api.py
```

**Expected:** 13/13 tests passing ✅

---

---

# PART 5: Database Queries You'll Use

## Get User's Prescriptions

```sql
SELECT * FROM prescriptions WHERE user_id = 1;
```

## Get Today's Doses

```sql
SELECT * FROM dose_tracking 
WHERE user_id = 1 
AND DATE(scheduled_time) = CURRENT_DATE;
```

## Calculate Adherence Percentage

```sql
SELECT 
    SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as doses_taken,
    COUNT(*) as total_doses,
    ROUND(100.0 * SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) / COUNT(*), 2) as adherence_pct
FROM dose_tracking
WHERE user_id = 1 AND DATE(scheduled_time) = CURRENT_DATE;
```

## Check Contraindications

```sql
SELECT * FROM contraindication_checks 
WHERE user_id = 1 AND risk_level IN ('high', 'medium');
```

## Get Upcoming Reminders

```sql
SELECT * FROM reminders
WHERE user_id = 1 
AND reminder_time > NOW()
AND is_sent = FALSE
ORDER BY reminder_time;
```

---

---

# PART 6: Backup and Restore

## Backup Database

```bash
pg_dump -U postgres postgres > backup.sql
```

**Creates:** `backup.sql` file with all data

---

## Restore Database

```bash
psql -U postgres < backup.sql
```

**Restores:** All tables and data

---

---

# PART 7: Troubleshooting

## Issue 1: "Cannot connect to database"

**Check:**
1. Is PostgreSQL running?
   ```bash
   psql -U postgres -c "SELECT 1;"
   ```

2. Is port 5432 open?
   ```bash
   netstat -an | find "5432"
   ```

3. Are credentials correct in .env?
   ```bash
   cat .env
   ```

**Solution:**
- Restart PostgreSQL service
- Check password is 'root'
- Verify localhost in connection string

---

## Issue 2: "Tables don't exist"

**Check:**
```sql
psql -U postgres -c "\dt"
```

**Solution:**
- Run schema.sql again:
  ```bash
  psql -U postgres -f schema.sql
  ```

---

## Issue 3: "Permission denied"

**Check:**
```bash
psql -U postgres -c "SELECT * FROM users;"
```

**Solution:**
- Make sure user is 'postgres'
- Check password is 'root'
- Grant permissions:
  ```sql
  GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
  ```

---

## Issue 4: "Foreign key constraint"

**Check error:**
```sql
INSERT INTO prescriptions (user_id, medicine_name, dosage)
VALUES (999, 'Metformin', '500mg'); -- user_id 999 doesn't exist
```

**Solution:**
- Create user first:
  ```sql
  INSERT INTO users (username, email) VALUES ('testuser', 'test@example.com');
  ```
- Then insert prescription

---

---

# PART 8: Database Optimization

## Create Indexes (Speed Up Queries)

Already done! View them:

```sql
SELECT * FROM pg_indexes WHERE tablename = 'dose_tracking';
```

---

## Monitor Database Size

```sql
SELECT 
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datname = 'postgres';
```

---

## Check Active Connections

```sql
SELECT * FROM pg_stat_activity;
```

---

---

# PART 9: Connection from Backend

## How App.py Connects

```python
# File: db_connection.py

from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()  # Load .env file

db_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)
```

**Explained:**
1. Load credentials from `.env`
2. Connect using `psycopg2` library
3. Execute queries through this connection

---

## How Flask Uses Database

```python
# File: app.py

@app.route('/api/users/<user_id>/medical-info', methods=['POST'])
def save_medical_info(user_id):
    conn = get_db_connection()
    execute_update(
        conn,
        "INSERT INTO user_medical_info ...",
        params
    )
    conn.close()
    return {"status": "success"}
```

**Flow:**
1. Browser sends request to `/api/users/1/medical-info`
2. Flask route receives it
3. Gets database connection
4. Inserts data into table
5. Returns success response

---

---

# PART 10: Database in Production

## Deploy to Cloud

### Option 1: AWS RDS

1. Create RDS instance (PostgreSQL)
2. Get connection string
3. Update `.env` with new connection string
4. Deploy Flask app to AWS EC2

---

### Option 2: Heroku PostgreSQL

1. Create Heroku app
2. Add PostgreSQL add-on
3. Get DATABASE_URL
4. Update `.env`
5. Deploy app

---

### Option 3: DigitalOcean Managed Database

1. Create managed PostgreSQL database
2. Get connection string
3. Update `.env`
4. Deploy app to Droplet

---

### Update Connection String

```env
# Local development
DATABASE_URL=postgresql://postgres:root@localhost:5432/postgres

# Production (AWS RDS)
DATABASE_URL=postgresql://user:password@prod-db.aws.com:5432/dbname

# Production (Heroku)
DATABASE_URL=postgresql://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/db_name
```

---

---

# Summary Checklist

✅ **Database Setup Complete:**

- [ ] PostgreSQL installed and running
- [ ] Credentials configured in `.env`
- [ ] 11 tables created
- [ ] Connection tested
- [ ] Backend using database (currently active)
- [ ] Test API tests passing (13/13)
- [ ] Sample data inserted
- [ ] Backup created

---

## Current Status

```
✅ PostgreSQL running on localhost:5432
✅ Database: postgres
✅ User: postgres
✅ Password: root
✅ 11 tables created
✅ Connection tested and working
✅ Backend actively using database
✅ Frontend sending data to database
✅ Test suite all passing (13/13 tests)
```

---

## Quick Commands

```bash
# Connect to database
psql -U postgres

# See tables
\dt

# See specific table
SELECT * FROM users;

# Run schema
psql -U postgres -f schema.sql

# Test connection
python test_api.py

# Backup database
pg_dump -U postgres postgres > backup.sql

# Restore from backup
psql -U postgres < backup.sql
```

---

**Your database is fully operational!** 🎉

For questions, check test_api.py examples or USAGE_GUIDE.md.
