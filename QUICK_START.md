# ⚡ Quick Start Guide - 5 Minutes to Running

## 🎯 One-Time Setup

### On Windows (Recommended)

1. **Open Command Prompt** in the project folder
   ```bash
   cd c:\Users\kumar\OneDrive\Documents\pro
   ```

2. **Run the startup script** (handles everything)
   ```bash
   start.bat
   ```

   This will:
   - ✅ Install Python packages
   - ✅ Create database tables
   - ✅ Start the Flask server

3. **Wait for this message**
   ```
   Running on http://127.0.0.1:5000
   ```

Done! The API is running.

---

## 🧪 Test That Everything Works

### In a New Terminal/Command Prompt

```bash
# Go to project folder
cd c:\Users\kumar\OneDrive\Documents\pro

# Run tests
python test_api.py
```

Expected result: **13/13 tests passed ✅**

---

## 🔗 Connect Your Replit Frontend

### In your Replit HTML/JavaScript:

```javascript
// Add this at the top of your JavaScript file
const API_BASE = 'http://localhost:5000';

// Example: Register a user
async function registerUser() {
    const response = await fetch(`${API_BASE}/api/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'john_doe',
            email: 'john@example.com',
            full_name: 'John Doe'
        })
    });
    
    const result = await response.json();
    console.log(result);
    return result.data.id;
}
```

---

## 📱 Basic API Workflow

### Step 1: Create User Account
```bash
curl -X POST http://localhost:5000/api/users/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"john\",\"email\":\"john@example.com\",\"full_name\":\"John Doe\"}"
```

**Response**: `user_id` = 1

### Step 2: Save Medical Info
```bash
curl -X POST http://localhost:5000/api/users/1/medical-info ^
  -H "Content-Type: application/json" ^
  -d "{\"drug_allergies\":\"Penicillin\",\"is_pregnant\":false}"
```

### Step 3: Upload Prescription
```bash
# OCR from image
curl -X POST http://localhost:5000/api/prescriptions/ocr ^
  -F "image=@prescription.jpg" ^
  -F "user_id=1"

# Or manual entry
curl -X POST http://localhost:5000/api/prescriptions/manual-entry ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":1,\"medicine_name\":\"Metformin\",\"dosage\":\"500\",\"dosage_unit\":\"mg\",\"frequency\":\"Twice daily\"}"
```

### Step 4: Get Medication Info (Plain Language!)
```bash
curl http://localhost:5000/api/medications/metformin
```

**Response includes**:
- ✅ What it's for
- ✅ How it works
- ✅ How to take it
- ✅ Why it's important (Nudge Theory)
- ✅ Risks of skipping

### Step 5: Check for Contraindications
```bash
curl -X POST http://localhost:5000/api/contraindications ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":1,\"medicine_name\":\"Metformin\"}"
```

### Step 6: Save Prescription & Create Plan
```bash
curl -X POST http://localhost:5000/api/prescriptions ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":1,\"medicine_name\":\"Metformin\",\"dosage\":\"500\",\"dosage_unit\":\"mg\",\"frequency\":\"Twice daily\",\"duration\":30,\"is_confirmed\":true}"
```

**Response**: `prescription_id` = 1

```bash
curl -X POST http://localhost:5000/api/adherence-plans ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":1,\"prescription_id\":1}"
```

### Step 7: Get Reminders
```bash
curl http://localhost:5000/api/reminders/upcoming/1
```

Response: Next 24 hours of doses to take

### Step 8: Track Doses
```bash
# User took the dose
curl -X POST http://localhost:5000/api/doses/1/mark-taken

# User missed the dose
curl -X POST http://localhost:5000/api/doses/1/mark-missed ^
  -H "Content-Type: application/json" ^
  -d "{\"reason\":\"Forgot\"}"
```

### Step 9: View Progress
```bash
curl http://localhost:5000/api/adherence-summary/1
```

Response:
- Today's doses taken
- Today's doses missed
- Today's adherence %
- Weekly trend
- Encouragement message 💪

---

## 📂 Important Files

| File | Purpose |
|------|---------|
| `app.py` | Main API code (all endpoints) |
| `db_connection.py` | Database utilities |
| `medication_kb.py` | Medication knowledge base |
| `ocr_processor.py` | OCR processing |
| `USAGE_GUIDE.md` | Complete API documentation |
| `REPLIT_INTEGRATION.md` | How to connect frontend |
| `test_api.py` | Run tests |

---

## 🔑 Key REST Endpoints

```
USER MANAGEMENT
POST   /api/users/register
GET    /api/users/<id>
POST   /api/users/<id>/medical-info

PRESCRIPTIONS
POST   /api/prescriptions/ocr
POST   /api/prescriptions/manual-entry
POST   /api/prescriptions

MEDICATION INFO
GET    /api/medications/<name>

SAFETY
POST   /api/contraindications
GET    /api/adherence/nudges/<id>

PLANS & REMINDERS
POST   /api/adherence-plans
GET    /api/reminders/upcoming/<id>
POST   /api/doses/<id>/mark-taken
POST   /api/doses/<id>/mark-missed

REPORTS
GET    /api/adherence-summary/<id>
GET    /api/reports/adherence/<id>

SYSTEM
GET    /api/health
GET    /api/disclaimer
```

---

## 🆘 Troubleshooting

### Problem: "python is not recognized"
- Python not installed
- **Solution**: Install Python 3.8+ from python.org

### Problem: "ModuleNotFoundError"
- Dependencies not installed
- **Solution**: Run `pip install -r requirements.txt`

### Problem: "Cannot Connect to PostgreSQL"
- Database not running
- **Solution**: Start PostgreSQL service (Windows: Services > PostgreSQL)
- **Or check**: `.env` file has correct credentials

### Problem: API returns 404
- Wrong endpoint URL
- **Solution**: Check URL spelling against USAGE_GUIDE.md

### Problem: "Address already in use"
- Another program using port 5000
- **Solution**: Kill the process or use different port (edit app.py line: `app.run(port=5001)`)

---

## 🚀 Next: Deploy to Production

When ready to go live with your Replit frontend:

1. **Follow REPLIT_INTEGRATION.md** for detailed steps
2. **Deploy backend to** Render.com or Railway.app (free tier)
3. **Update API_BASE** in frontend to use deployed URL
4. **Test everything** with the test suite again

---

## 📞 Support Resources

- **API Documentation**: See `USAGE_GUIDE.md`
- **Frontend Integration**: See `REPLIT_INTEGRATION.md`
- **Project Overview**: See `PROJECT_COMPLETE.md`
- **Database Schema**: See `schema.sql`

---

## ✅ Success Checklist

- [ ] Flask server running
- [ ] All 13 tests passing
- [ ] Created test user via API
- [ ] Saved medical information
- [ ] Uploaded/entered prescription
- [ ] Got plain language medication explanation
- [ ] Created adherence plan
- [ ] Can toggle dose as taken/missed
- [ ] Frontend API calls working
- [ ] Ready to deploy!

---

**Everything is ready to use! 🎉**

Start with `start.bat` now! →
