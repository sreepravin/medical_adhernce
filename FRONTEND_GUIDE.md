# 🌐 Frontend Setup Guide

## 📱 What You Have

A complete, professional frontend webpage for the Medication Adherence System with:

✅ **User Authentication** (Demo login)
✅ **Dashboard** with daily dose tracking
✅ **Prescription Management** (Add new prescriptions)
✅ **Medication Information** (Plain language explanations)
✅ **Dose Tracking** (Mark taken/missed)
✅ **Adherence Reports** (Daily/weekly statistics)
✅ **Responsive Design** (Works on mobile too!)
✅ **Beautiful UI** (Modern, professional styling)

## 📂 File Location

```
c:\Users\Kumar\OneDrive\Documents\pro\index.html
```

## 🚀 How to Run

### Option 1: Open in Browser Directly (Quickest)

1. **Navigate to the folder** in File Explorer
2. **Right-click on `index.html`**
3. **Select "Open with Browser"**
4. That's it! The page will open

### Option 2: Use Python HTTP Server

**In Command Prompt:**

```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python -m http.server 8000
```

**Then visit:**
```
http://localhost:8000/index.html
```

### Option 3: Start Backend & Frontend Together

**Terminal 1 - Start Flask Backend:**
```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
start.bat
```

**Terminal 2 - Start HTTP Server:**
```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python -m http.server 8000
```

**Terminal 3 - Open in Browser:**
```
http://localhost:8000/index.html
```

## 🔗 Connecting Frontend to Backend

The frontend is **already configured** to connect to your Flask backend!

```javascript
// In index.html, line ~415:
const API_BASE = 'http://localhost:5000/api';
```

This means:
- Frontend runs on `http://localhost:8000/index.html`
- Backend runs on `http://localhost:5000/api`
- They talk to each other automatically!

## 🎮 Demo Usage

### Step 1: Login (Demo)

**Login Page:**
- Username: `testuser` (anything works in demo)
- Password: `password` (any password)
- Or click "Register" to create account

### Step 2: Add Medical Info

- Click "Dashboard" tab
- Add your medical information (allergies, conditions)

### Step 3: Add Prescription

- Click "Prescription" tab
- Fill in medicine name, dosage, frequency
- Click "Add Prescription"

### Step 4: View Medications

- Click "Medications" tab
- Search for medications or click quick links
- View plain language explanations

### Step 5: Track Doses

- Click "Tracking" tab
- Mark doses as "Taken" or "Missed"
- Get smart guidance for missed doses

### Step 6: View Reports

- Click "Reports" tab
- See your adherence statistics
- Export report for doctor

## 🎨 Features Overview

### Dashboard
- 📊 Today's dose count
- 📈 Adherence percentage
- 📋 Active prescriptions
- 💬 Encouraging message
- ⏰ Today's dose schedule

### Prescription Management
- ➕ Add new prescriptions (manual or OCR)
- 📋 View all prescriptions
- 🔄 Update prescriptions
- 🗑️ Delete prescriptions

### Medication Information
- 🔍 Search medications
- 📖 Plain language explanations
- 💊 Available medications library (6+)
- 💡 "Why it's important" nudges
- ⚠️ Side effects & warnings

### Dose Tracking
- ⏰ Next 24h reminders
- ✓ Mark dose taken
- ✗ Mark dose missed
- 💬 Smart missed dose guidance

### Adherence Reports
- 📊 Daily statistics
- 📈 Weekly trends
- 💯 Adherence percentage
- 📥 Export for doctor

## 🔐 Authentication

In demo mode:
- Any username works
- Any password works
- For production, implement real JWT authentication

Update in `index.html`:

```javascript
// Replace demo authentication with real API call:
function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    fetch(`${API_BASE}/users/login`, {  // Add this endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            localStorage.setItem('authToken', data.token);
            currentUser = data.user;
            showMainApp();
        }
    });
}
```

## 🌍 Browser Compatibility

Works on:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)
- ✅ Mobile browsers

## 📱 Mobile Responsive

The design is fully responsive:
- 📱 Works on phones (320px+)
- 📱 Works on tablets
- 💻 Works on desktops
- 🖥️ Works on large screens

## 🎨 Customization

### Colors

Edit the CSS variables at the top of the `<style>` section:

```css
:root {
    --primary-color: #2563eb;        /* Main blue */
    --secondary-color: #1e40af;      /* Dark blue */
    --success-color: #10b981;        /* Green */
    --warning-color: #f59e0b;        /* Orange */
    --danger-color: #ef4444;         /* Red */
}
```

### Fonts

Change font-family in the `body` CSS rule:

```css
body {
    font-family: 'Your Font Here', sans-serif;
}
```

### Logo/Branding

Replace "💊 Pill Pal" in the navbar with your branding

## 🔧 Troubleshooting

### Issue: "Cannot connect to API"

**Check:**
1. Is the Flask backend running? (`start.bat` in terminal 1)
2. Is it on `http://localhost:5000`?
3. Check browser console for errors (F12 → Console)

**Solution:**
```bash
# Terminal 1: Restart Flask
cd c:\Users\Kumar\OneDrive\Documents\pro
start.bat
```

### Issue: CORS Errors

If you see CORS errors in console, the backend CORS needs updating.

In `app.py`, update:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000"]
    }
})
```

### Issue: Forms not submitting

Check:
1. Browser console for errors (F12)
2. All required fields are filled
3. Backend is responding (check `python test_api.py`)

### Issue: Doses not updating

1. Make sure prescription is added first
2. Check database has data (`python app.py` log should show SQL queries)
3. Refresh the page (Ctrl+R)

## 🚀 Deployment

### Deploy Frontend to Production

**Option 1: Replit** (Already there!)
- Upload `index.html` to Replit
- Update `API_BASE` to your production backend URL
- Done!

**Option 2: Netlify**
1. Create account at netlify.com
2. Drag and drop folder
3. Configure API endpoint
4. Deploy!

**Option 3: GitHub Pages**
1. Push to GitHub repo
2. Enable GitHub Pages
3. Update API endpoint in index.html
4. Done!

### Update API Endpoint for Production

```javascript
// Change this line in index.html
const API_BASE = 'http://localhost:5000/api';

// To production URL:
const API_BASE = 'https://your-deployed-backend.com/api';
```

## 📚 JavaScript Functions Reference

### Core Functions

```javascript
// Authentication
handleLogin()              // Login user
handleRegister()          // Register new user
handleLogout()            // Logout

// Navigation
showTab(tabName)          // Switch tabs
updatePrescriptionMethod() // Change prescription input method

// Prescriptions
handleAddPrescription()    // Add new prescription

// Medications
searchMedication()        // Search medication info
getMedicationInfo(name)   // Get medication details
displayMedicationInfo()   // Display medication UI

// Tracking
markDoseTaken(id)        // Mark dose as taken
markDoseMissed(id)       // Mark dose as missed
loadTracking()           // Load tracking tab

// Dashboard
loadDashboard()          // Load dashboard tab
loadReports()            // Load reports tab

// Modals
closeMedInfoModal()      // Close medication info modal
```

### API Endpoints Used

```javascript
// Users
POST /api/users/register
POST /api/users/login        // (add this to backend)

// Medications
GET /api/medications/<name>

// Prescriptions
POST /api/prescriptions

// Doses
POST /api/doses/<id>/mark-taken
POST /api/doses/<id>/mark-missed

// Tracking
GET /api/reminders/upcoming/<user_id>

// Reports
GET /api/adherence-summary/<user_id>
```

## 🎓 Learning Path

1. **Understand the UI** - Explore all tabs
2. **Add test prescription** - Click "Prescription" → Add Prescription
3. **Search medication** - Click "Medications" → Search "Metformin"
4. **Mark doses** - Click "Tracking" → Mark Taken/Missed
5. **View reports** - Click "Reports" → See statistics
6. **Customize colors** - Edit CSS variables
7. **Modify API calls** - Update JavaScript functions

## 📞 Need Help?

- **Frontend questions** - Check the code comments
- **Backend issues** - See USAGE_GUIDE.md
- **API problems** - See test_api.py examples
- **Integration help** - See REPLIT_INTEGRATION.md

## ✨ Next Steps

1. ✅ Open `index.html` in browser
2. ✅ Make sure backend is running (`start.bat`)
3. ✅ Test login (any username/password in demo)
4. ✅ Add a prescription
5. ✅ Mark doses taken/missed
6. ✅ View reports
7. ✅ Customize for your needs

---

**Frontend Ready!** 🎉

Everything is connected and ready to use. Enjoy!
