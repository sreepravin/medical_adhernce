# Medication Adherence Support System - Complete Setup Guide

## 📋 System Overview

This is a comprehensive medication adherence support system that:
- 📸 Processes prescription images via OCR
- 🔤 Converts medical jargon to plain language
- 🎯 Creates personalized adherence plans using behavioral science (Nudge Theory)
- ⚠️ Checks for drug contraindications and allergies
- ⏰ Provides intelligent reminders and tracks adherence
- 📊 Generates adherence reports for healthcare providers

## 🏗️ System Architecture

```
Frontend (Replit) → Flask API (Backend) → PostgreSQL Database
```

## 📁 Project Files

```
pro/
├── app.py                    # Main Flask API
├── db_connection.py         # Database utilities
├── medication_kb.py         # Medication knowledge base & plain language translator
├── ocr_processor.py         # OCR and image processing
├── schema.sql               # Database schema
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (keep secret!)
├── .env.example            # Template for .env
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Database

First, create the database tables in PostgreSQL:

```bash
psql -h localhost -U postgres -d postgres < schema.sql
```

Or connect to your PostgreSQL and run the SQL commands manually.

### Step 3: Configure Environment Variables

Create a `.env` file with your database credentials:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=root
```

### Step 4: Run the Flask Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## 📡 API Endpoints

### User Management

#### Register User
```
POST /api/users/register
{
  "username": "string",
  "email": "string",
  "full_name": "string"
}
```

#### Get User Profile
```
GET /api/users/<user_id>
```

#### Save Medical Information
```
POST /api/users/<user_id>/medical-info
{
  "drug_allergies": "string",
  "food_allergies": "string",
  "existing_conditions": "string",
  "current_medications": "string",
  "is_pregnant": boolean,
  "is_breastfeeding": boolean
}
```

#### Get Medical Information
```
GET /api/users/<user_id>/medical-info
```

### Prescription Processing

#### Process Prescription Image (OCR)
```
POST /api/prescriptions/ocr
Content-Type: multipart/form-data

Fields:
- image: [image file]
- user_id: integer
```

Response:
```json
{
  "medicine_name": "string",
  "dosage": "string",
  "dosage_unit": "string",
  "frequency": "string",
  "duration": integer,
  "route": "string",
  "ocr_confidence": float,
  "extraction_notes": []
}
```

#### Manual Prescription Entry
```
POST /api/prescriptions/manual-entry
{
  "user_id": integer,
  "medicine_name": "string",
  "dosage": "string",
  "dosage_unit": "mg",
  "frequency": "string",
  "duration": integer,
  "route": "oral",
  "instructions": "string",
  "prescribed_by": "string"
}
```

#### Save Prescription
```
POST /api/prescriptions
{
  "user_id": integer,
  "medicine_name": "string",
  "dosage": "string",
  "dosage_unit": "string",
  "frequency": "string",
  "duration": integer,
  "start_date": "YYYY-MM-DD",
  "route": "string",
  "instructions": "string",
  "prescribed_by": "string",
  "is_confirmed": boolean
}
```

### Medication Understanding

#### Get Medication Information (Plain Language)
```
GET /api/medications/<medicine_name>
```

Response:
```json
{
  "medicine_name": "string",
  "generic_name": "string",
  "what_for": "string",
  "how_works": "string",
  "how_to_take": "string",
  "with_food": "string",
  "side_effects": "string",
  "plain_language_explanation": "string"
}
```

### Adherence Plans

#### Create Adherence Plan
```
POST /api/adherence-plans
{
  "prescription_id": integer,
  "user_id": integer
}
```

Response:
```json
{
  "plan_id": integer,
  "prescription_id": integer,
  "daily_schedule": ["08:00", "20:00"],
  "why_important": "string",
  "nudges": [
    {
      "title": "string",
      "message": "string",
      "type": "motivation|completion|consequence"
    }
  ]
}
```

#### Get Adherence Plan
```
GET /api/adherence-plans/<plan_id>
```

### Contraindications & Safety

#### Check Drug Contraindications
```
POST /api/contraindications
{
  "user_id": integer,
  "medicine_name": "string"
}
```

Response:
```json
{
  "medicine_name": "string",
  "warnings": [
    {
      "type": "ALLERGY|PREGNANCY|BREASTFEEDING|CONDITION",
      "risk": "HIGH|MEDIUM|LOW",
      "message": "string",
      "action": "string"
    }
  ],
  "has_warnings": boolean,
  "requires_confirmation": boolean
}
```

#### Get Adherence Nudges
```
GET /api/adherence/nudges/<prescription_id>
```

#### Get Safety Disclaimer
```
GET /api/disclaimer
```

### Reminders & Dose Tracking

#### Get Upcoming Reminders
```
GET /api/reminders/upcoming/<user_id>
```

#### Mark Dose as Taken
```
POST /api/doses/<dose_id>/mark-taken
```

#### Mark Dose as Missed
```
POST /api/doses/<dose_id>/mark-missed
{
  "reason": "string"
}
```

Response includes guidance on whether to take the missed dose.

### Monitoring & Reports

#### Get Adherence Summary
```
GET /api/adherence-summary/<user_id>
```

Response:
```json
{
  "today": {
    "doses_taken": integer,
    "doses_missed": integer,
    "total_doses": integer,
    "adherence_percentage": float
  },
  "weekly_summary": [
    {
      "date": "YYYY-MM-DD",
      "doses_taken": integer,
      "doses_missed": integer,
      "total_doses": integer,
      "adherence_percentage": float
    }
  ],
  "encouragement": "string"
}
```

#### Export Adherence Report
```
GET /api/reports/adherence/<user_id>
```

### System Health

#### Health Check
```
GET /api/health
```

## 🔄 Typical User Flow

### 1. User Registration
```bash
curl -X POST http://localhost:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe"
  }'
```

### 2. Save Medical Information
```bash
curl -X POST http://localhost:5000/api/users/1/medical-info \
  -H "Content-Type: application/json" \
  -d '{
    "drug_allergies": "Penicillin",
    "existing_conditions": "Diabetes, High Blood Pressure",
    "is_pregnant": false
  }'
```

### 3. Upload or Enter Prescription
**Option A: Upload Image**
```bash
curl -X POST http://localhost:5000/api/prescriptions/ocr \
  -F "image=@prescription.jpg" \
  -F "user_id=1"
```

**Option B: Manual Entry**
```bash
curl -X POST http://localhost:5000/api/prescriptions/manual-entry \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "medicine_name": "Metformin",
    "dosage": "500",
    "dosage_unit": "mg",
    "frequency": "Twice daily",
    "duration": 30
  }'
```

### 4. Get Plain Language Explanation
```bash
curl http://localhost:5000/api/medications/metformin
```

### 5. Check Contraindications
```bash
curl -X POST http://localhost:5000/api/contraindications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "medicine_name": "Metformin"
  }'
```

### 6. Save Prescription & Create Adherence Plan
```bash
curl -X POST http://localhost:5000/api/prescriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "medicine_name": "Metformin",
    "dosage": "500",
    "dosage_unit": "mg",
    "frequency": "Twice daily",
    "duration": 30,
    "is_confirmed": true
  }'

# Response will include prescription_id

curl -X POST http://localhost:5000/api/adherence-plans \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_id": 1,
    "user_id": 1
  }'
```

### 7. Get Upcoming Reminders
```bash
curl http://localhost:5000/api/reminders/upcoming/1
```

### 8. Track Doses
```bash
# Mark dose as taken
curl -X POST http://localhost:5000/api/doses/1/mark-taken

# Mark dose as missed
curl -X POST http://localhost:5000/api/doses/1/mark-missed \
  -H "Content-Type: application/json" \
  -d '{"reason": "Forgot to take it"}'
```

### 9. View Adherence Summary
```bash
curl http://localhost:5000/api/adherence-summary/1
```

### 10. Export Report for Doctor
```bash
curl http://localhost:5000/api/reports/adherence/1
```

## 🔧 Configuration

### Available Medications in Knowledge Base
The system comes with knowledge base entries for:
- Aspirin
- Metformin
- Amoxicillin
- Lisinopril
- Ibuprofen
- Atorvastatin

To add more medications, edit `medication_kb.py` and add entries to the `MEDICATION_DATABASE` dictionary.

### Supported Dose Frequencies
- Once a day / Once daily
- Twice a day / Twice daily
- Three times a day / Three times daily
- Every X hours (8, 12, 6 hour intervals)
- At bedtime
- Before breakfast
- After meals

### Drug Interactions
Basic drug interaction checking is implemented in `medication_kb.py`. Expand the `DRUG_INTERACTIONS` dictionary to add more interactions.

## 🔐 Security Considerations

1. **Always keep `.env` file secret** - Never commit it to version control
2. **Use HTTPS in production** - Always use SSL/TLS
3. **Implement authentication** - Add JWT or session-based auth
4. **Validate all inputs** - The system validates but always be careful
5. **Rate limiting** - Add rate limiting for production use
6. **HIPAA Compliance** - Ensure compliance if handling protected health info

## 🐛 Troubleshooting

### OCR Issues
- Ensure image is clear and well-lit
- Try with different image formats (PNG, JPG)
- Check pytesseract installation: `python -c "import pytesseract; print('OK')"`

### Database Connection Issues
```python
# Test connection
from db_connection import get_db_connection
conn = get_db_connection()
if conn:
    print("Connected!")
    conn.close()
else:
    print("Connection failed")
```

### Module Import Errors
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

## 📊 Database Schema

Key tables:
- **users**: Patient/user information
- **user_medical_info**: Allergies, conditions, medications
- **prescriptions**: Medication prescriptions
- **adherence_plans**: Personalized adherence schedules
- **dose_tracking**: Individual dose logs
- **contraindication_checks**: Safety warnings
- **reminders**: Notification tracking
- **adherence_summary**: Daily/weekly aggregated data

## 🌐 Connecting to Replit Frontend

To connect to your Replit frontend at `https://pill-pal--akashc2005.replit.app`:

1. Update Flask CORS settings to allow Replit domain:
```python
CORS(app, origins=['https://pill-pal--akashc2005.replit.app'])
```

2. Use the API base URL in your frontend:
```javascript
const API_BASE = 'http://localhost:5000'; // For local testing
// or
const API_BASE = 'https://your-deployed-backend.com'; // For production
```

3. Deploy the Flask backend to a service like:
   - Render.com
   - Railway.app
   - Heroku
   - AWS
   - DigitalOcean

## 📝 Additional Notes

- The system provides **informational support only** - always consult healthcare providers
- Doses are scheduled starting at the `start_date` of the prescription
- Adherence is calculated as (doses_taken / total_doses) * 100
- Encouragement messages adapt based on adherence percentage

## 🚨 Safety Disclaimer

**THIS SYSTEM IS NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE**

Always consult with your healthcare provider:
- Before starting any medication
- If experiencing side effects
- Before stopping medication
- For any health concerns

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API endpoints documentation
3. Check database schema for data structure
4. Review medication knowledge base for available medications

---

**Last Updated**: February 6, 2026
