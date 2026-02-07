# Email Configuration Guide for Medical Support

The report export feature is now **ready to send emails**! Follow these steps to configure your email:

## Quick Setup (Gmail - Recommended)

### Step 1: Enable 2-Factor Authentication on Gmail
1. Go to https://myaccount.google.com/security
2. In the left menu, click **Security**
3. Enable **2-Step Verification** (if not already enabled)

### Step 2: Create an App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or your device)
3. Click **Generate**
4. Copy the 16-character password (it will be displayed once)

### Step 3: Update .env File
Edit the `.env` file in your project and update:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

Replace:
- `your-email@gmail.com` with your actual Gmail address
- `xxxx xxxx xxxx xxxx` with the 16-character app password you just generated

**Important**: Use the **app password**, not your regular Gmail password!

### Step 4: Restart the Flask Server
1. Stop the current Flask server (Ctrl+C)
2. Run `python app.py` again
3. Users can now export reports directly to their email!

---

## Configuration for Other Email Providers

### Outlook/Hotmail
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_EMAIL=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Yahoo Mail
```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_EMAIL=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```
(Yahoo also requires app-specific passwords)

### Office 365
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_EMAIL=your-email@company.onmicrosoft.com
SMTP_PASSWORD=your-password
```

### Custom SMTP Server
```
SMTP_SERVER=your-mail-server.com
SMTP_PORT=587
SMTP_EMAIL=your-email@domain.com
SMTP_PASSWORD=your-password
```

---

## Testing Your Configuration

After updating `.env` and restarting Flask, run:

```bash
python test_email_export.py
```

Expected output if configured correctly:
```
Response Status: 200
{
  "data": {
    "email_sent": true,
    "message": "Report successfully sent to sree@example.com",
    ...
  },
  "message": "Report emailed successfully",
  "status": "success"
}

✓ SUCCESS: Email sent successfully!
```

---

## Troubleshooting

### "Email not configured" or "email_sent: false"
- Check that `SMTP_EMAIL` and `SMTP_PASSWORD` are set in `.env`
- Verify they're not empty strings
- Restart Flask: Stop server (Ctrl+C) and run `python app.py` again

### "Authentication failed" / "Invalid credentials"
- For Gmail: Make sure you're using an **app-specific password**, not your regular password
- For other providers: Double-check username and password
- Ensure 2-Factor Authentication is enabled (if required by provider)

### "Connection refused" / "Cannot connect to SMTP server"
- Verify SMTP_SERVER and SMTP_PORT are correct
- Check your internet connection
- Some firewalls block SMTP port 587 - try port 465 (SMTP_PORT=465)

### Email arrives in spam
- Gmail: Click "Not Spam" to improve delivery
- Check sender reputation of your email account
- Consider using a business Gmail account

---

## How Users Export Reports

1. User logs in to the dashboard
2. Go to **Reports** tab
3. Click **Export for Doctor** button
4. Enter their email address
5. Click **Send Report**
6. Email arrives in their inbox within seconds!

The report includes:
- Today's medication adherence
- Current medications and dosages
- Weekly adherence breakdown
- Healthcare provider share link

---

**Questions?** Ensure .env is in the same directory as `app.py` and restart Flask after making changes!
