# ⚡ RUN_ME_FIRST.md - Quick Start (5 Minutes)

## 🎯 Goal: Get Everything Running Now

Follow these exact steps - takes 5 minutes!

---

## Step 1️⃣: Start the Flask Backend

**Open Command Prompt** and run:

```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
start.bat
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

✅ Leave this window open!

---

## Step 2️⃣: Open the Frontend

**In File Explorer:**

1. Navigate to: `c:\Users\Kumar\OneDrive\Documents\pro`
2. Find `index.html`
3. Right-click → **Open with** → **Your Browser** (Chrome/Firefox/Edge)

**Or in Command Prompt:**

```bash
start index.html
```

✅ The website opens in your browser!

---

## Step 3️⃣: Test It Out

### Login (Demo Mode)
- Username: `testuser` (anything works)
- Password: `password` (anything works)
- Click "Login"

### Add a Prescription
1. Click **"Prescription"** tab
2. Fill in:
   - Medicine: `Metformin`
   - Dosage: `500mg`
   - Frequency: `2 times daily`
   - Duration: `30 days`
3. Click **"Add Prescription"**

### Mark a Dose
1. Click **"Tracking"** tab
2. Click **"Mark as Taken"** on any dose
3. ✅ Dose recorded!

### View Report
1. Click **"Reports"** tab
2. See your adherence statistics
3. 📊 Data displayed!

---

## 🎨 What You See

| Tab | What's There |
|-----|--------------|
| 📊 Dashboard | Daily dose count, adherence %, active meds |
| 💊 Prescription | Add/manage prescriptions |
| 📖 Medications | Search and learn about medicines |
| ⏰ Tracking | Mark doses taken/missed |
| 📈 Reports | Statistics and trends |

---

## ✨ Features You Can Try

### 1. Browse Medications
- Click **"Medications"** tab
- Search: `Aspirin`, `Metformin`, `Amoxicillin`
- See plain language explanations

### 2. Check Warnings
- Click drop-down, go through medicines
- See "Side Effects" & "Important Warnings"

### 3. Track Adherence
- Mark doses daily in **"Tracking"** tab
- Watch adherence % go up in **"Reports"**

### 4. Get Nudges
- Smart messages based on your adherence
- Health reminders personalized to you

---

## 🔧 If Something Doesn't Work

### Issue ❌: Backend not starting

**Solution:**
```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
pip install -r requirements.txt
python app.py
```

### Issue ❌: Can't find index.html

**Path:** `c:\Users\Kumar\OneDrive\Documents\pro\index.html`

### Issue ❌: API errors in browser console (F12)

**Check:**
- Is backend (`start.bat`) running in terminal?
- Is it on port 5000?
- Any error messages? Check USAGE_GUIDE.md

### Issue ❌: Database connection error

**Solution:**
```bash
# Make sure PostgreSQL is running:
# Windows: Services → PostgreSQL → Start

# Check credentials in .env file:
cat .env
# Should show: DATABASE_URL=postgresql://postgres:root@localhost:5432/postgres
```

---

## 📁 File Structure

```
c:\Users\Kumar\OneDrive\Documents\pro\
├── index.html              ← Open this in browser! 🌐
├── app.py                  ← Flask backend
├── start.bat               ← Run this first! 🚀
├── requirements.txt        ← Dependencies
├── .env                    ← Database credentials
├── schema.sql              ← Database tables
├── medication_kb.py        ← Medicine database
├── ocr_processor.py        ← Image processing
├── db_connection.py        ← Database connection
├── test_api.py             ← Tests (run: python test_api.py)
└── [documentation files]
```

---

## 🚀 Two-Terminal Setup (Advanced)

**Terminal 1 - Backend:**
```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
start.bat
```

**Terminal 2 - Frontend Server:**
```bash
cd c:\Users\Kumar\OneDrive\Documents\pro
python -m http.server 8000
```

**Then open:** `http://localhost:8000/index.html`

---

## ✅ Quick Checklist

- [ ] Command Prompt open
- [ ] Ran `start.bat`
- [ ] See "Running on http://127.0.0.1:5000" message
- [ ] Opened `index.html` in browser
- [ ] See login page with "Pill Pal" branding
- [ ] Logged in (any username/password)
- [ ] See dashboard with today's stats
- [ ] Added a prescription
- [ ] Marked a dose taken
- [ ] Clicked "Reports" and saw stats
- [ ] ✨ Everything working!

---

## 🎯 Next Steps After Getting It Running

1. **Read USAGE_GUIDE.md** - All API endpoints explained
2. **Run `python test_api.py`** - Verify all features work
3. **Read ARCHITECTURE.md** - Understand how system works
4. **Customize colors** - Edit CSS in index.html
5. **Deploy** - Follow REPLIT_INTEGRATION.md

---

## 👀 System Currently Running

```
Frontend:  http://localhost:8000/index.html (from browser)
Backend:   http://localhost:5000/api (running in Terminal)
Database:  PostgreSQL on localhost:5432
```

**Everything connected and talking to each other!** 🎉

---

## 📊 Demo Data Available

**Medications (6 available to search):**
- Aspirin
- Metformin
- Amoxicillin
- Lisinopril
- Ibuprofen
- Atorvastatin

**Try searching them in the "Medications" tab!**

---

## 🆘 Help Resources

| Question | Answer |
|----------|--------|
| How to... add prescription? | Click "Prescription" tab → Fill form → Click "Add" |
| How to... mark dose taken? | Click "Tracking" tab → Click "Mark as Taken" |
| How to... see my stats? | Click "Reports" tab → See charts |
| How to... search medicines? | Click "Medications" tab → Use search box |
| How to... logout? | Click "Logout" button in top-right |
| Where are API docs? | See USAGE_GUIDE.md |
| How does system work? | See ARCHITECTURE.md |
| How to deploy? | See REPLIT_INTEGRATION.md |

---

## 🎓 Learning Resources in This Project

1. **QUICK_START.md** - 5-minute overview
2. **FRONTEND_GUIDE.md** - Complete frontend documentation
3. **USAGE_GUIDE.md** - All API endpoints with examples
4. **ARCHITECTURE.md** - System design and data flow
5. **REPLIT_INTEGRATION.md** - Frontend deployment guide
6. **test_api.py** - Running examples you can copy

---

## 💡 Tips

- **Pro Tip 1:** Demo mode stores data in localStorage (browser storage)
- **Pro Tip 2:** Refresh page to see real database updates
- **Pro Tip 3:** Open F12 (browser devtools) to see API calls in Network tab
- **Pro Tip 4:** Check backend logs in terminal to debug issues
- **Pro Tip 5:** Run tests with `python test_api.py` to verify everything

---

## 🎉 You're Ready!

```
1. start.bat        → Backend running ✅
2. Open index.html  → Frontend open ✅
3. Login            → Ready to use ✅
4. Add prescription → Test system ✅
5. Mark doses       → Track adherence ✅
```

**That's it! Enjoy your Medication Adherence System!** 🚀

---

**Questions?**
- Check the docs in this folder
- Run `python test_api.py` to verify setup
- All code is well-commented for learning
- Follow FRONTEND_GUIDE.md for browser troubleshooting

**Happy tracking!** 💊✨
