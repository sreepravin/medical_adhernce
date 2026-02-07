# Integration Guide: Connecting to Replit Frontend

This guide explains how to connect the Flask backend to your Replit frontend at:
**https://pill-pal--akashc2005.replit.app**

## 🔗 Local Development Setup

### Option 1: Backend on Localhost + Replit Frontend

If your Replit frontend is published and you want to test locally:

#### Step 1: Update Flask CORS Settings

Edit `app.py` and update the CORS configuration:

```python
from flask_cors import CORS

# Allow Replit frontend to make requests
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://pill-pal--akashc2005.replit.app",
            "http://localhost:3000",  # Your local frontend (if any)
            "http://localhost:5000"   # Your local backend
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

#### Step 2: Configure Frontend API URL

In your Replit frontend code, set the API base URL:

```javascript
// For development (local testing)
const API_BASE = 'http://localhost:5000';

// For production (deployed backend)
// const API_BASE = 'https://your-deployed-backend.com';

// Example API call
async function registerUser(username, email, fullName) {
    const response = await fetch(`${API_BASE}/api/users/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            email: email,
            full_name: fullName
        })
    });
    return await response.json();
}
```

#### Step 3: Use ngrok for Public URL (Optional)

To expose your local Flask server publicly while testing with Replit:

```bash
# Install ngrok (https://ngrok.com)
ngrok http 5000

# This gives you a public URL like: https://abc123xyz.ngrok.io
# Update your frontend API_BASE to this URL
```

## 🚀 Production Deployment

To permanently connect your backend to the Replit frontend:

### Option 1: Deploy Backend to Render.com (Recommended)

**Benefits**: Free tier available, easy integration, PostgreSQL support

#### Steps:

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Connect Repository**
   - Create a GitHub repository for this project
   - Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

3. **Deploy Flask App**
   - On Render.com, click "New" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     ```
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn app:app
     Environment Variables:
       - DB_HOST=<your-postgres-host>
       - DB_PORT=5432
       - DB_NAME=<your-db-name>
       - DB_USER=<your-db-user>
       - DB_PASSWORD=<your-db-password>
     ```

4. **Update Frontend API URL**
   ```javascript
   const API_BASE = 'https://your-app-name.onrender.com';
   ```

### Option 2: Deploy Backend to Railway.app

**Benefits**: PostgreSQL database included, easy to use

#### Steps:

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub"

3. **Add PostgreSQL Database**
   - In your project, click "Add Service"
   - Select "PostgreSQL"
   - Railway will provide connection details

4. **Deploy Python App**
   - Configure environment variables with PostgreSQL details
   - Railway will auto-detect Flask app and deploy

5. **Update Frontend API URL**
   ```javascript
   const API_BASE = 'https://your-railway-app.up.railway.app';
   ```

### Option 3: Deploy to Heroku (Legacy)

Note: Heroku free tier has been discontinued, but the service still exists.

### Option 4: Deploy to AWS

For more advanced deployments with full control.

## 🔀 CORS Configuration Checklist

Make sure your backend allows requests from Replit:

- ✅ Replit frontend domain is in CORS origins
- ✅ Content-Type header is allowed
- ✅ OPTIONS requests are handled (Flask-CORS does this automatically)
- ✅ Credentials are configured if using authentication

Example CORS headers that should be returned:
```
Access-Control-Allow-Origin: https://pill-pal--akashc2005.replit.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## 📡 Frontend Integration Examples

### Register User Example
```javascript
async function handleUserRegistration() {
    const formData = {
        username: 'john_doe',
        email: 'john@example.com',
        full_name: 'John Doe'
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            console.log('User registered:', result.data);
            localStorage.setItem('userId', result.data.id);
        } else {
            console.error('Registration failed:', result.error);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}
```

### Upload Prescription Image Example
```javascript
async function handlePrescriptionUpload(imageFile, userId) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('user_id', userId);
    
    try {
        const response = await fetch(`${API_BASE}/api/prescriptions/ocr`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            console.log('Prescription extracted:', result.data);
            // Show user the extracted data for confirmation
        }
    } catch (error) {
        console.error('Upload error:', error);
    }
}
```

### Get Medication Information Example
```javascript
async function showMedicationInfo(medicineName) {
    try {
        const response = await fetch(`${API_BASE}/api/medications/${medicineName}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const med = result.data;
            console.log(`What it's for: ${med.what_for}`);
            console.log(`How it works: ${med.how_works}`);
            console.log(`Plain language explanation:\n${med.plain_language_explanation}`);
        }
    } catch (error) {
        console.error('Error fetching medication info:', error);
    }
}
```

### Create Adherence Plan Example
```javascript
async function createAdheren​cePlan(userId, prescriptionId) {
    try {
        const response = await fetch(`${API_BASE}/api/adherence-plans`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                prescription_id: prescriptionId
            })
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            const plan = result.data;
            console.log('Daily schedule:', plan.daily_schedule);
            console.log('Why important:', plan.why_important);
            console.log('Behavioral nudges:', plan.nudges);
        }
    } catch (error) {
        console.error('Error creating plan:', error);
    }
}
```

## 🔐 Security Considerations for Frontend Integration

1. **Never expose secrets in frontend code**
   - Keep DB_PASSWORD and API keys on backend only
   
2. **Implement authentication**
   - Add JWT tokens or session-based auth to backend
   - Frontend should include token in Authorization header
   
3. **Validate all inputs on backend**
   - Don't trust frontend validation
   
4. **Use HTTPS in production**
   - Your backend should use SSL/TLS
   - Replit frontend is already on HTTPS
   
5. **Rate limit API requests**
   - Prevent abuse and unauthorized access

Example with JWT authentication:
```python
# Backend: Generate token on login
from flask_jwt_extended import JWTManager, create_access_token

jwt = JWTManager(app)

@app.route('/api/users/login', methods=['POST'])
def login():
    # Validate credentials...
    access_token = create_access_token(identity=user_id)
    return jsonify(access_token=access_token)

# Backend: Protect endpoints
from flask_jwt_extended import jwt_required

@app.route('/api/adherence-summary/<int:user_id>')
@jwt_required()
def get_adherence_summary(user_id):
    # Only execute if valid token
    ...
```

```javascript
// Frontend: Include token in requests
async function getAdherenceSummary(userId, token) {
    const response = await fetch(
        `${API_BASE}/api/adherence-summary/${userId}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );
    return await response.json();
}
```

## 🧪 Testing Integration

Before deploying to production:

1. **Test locally**
   ```bash
   python start.bat  # Windows
   # In another terminal:
   python test_api.py
   ```

2. **Test CORS**
   ```javascript
   // In browser console at https://pill-pal--akashc2005.replit.app
   fetch('http://localhost:5000/api/health').then(r => r.json()).then(console.log);
   ```

3. **Test with deployed backend**
   - Deploy backend first
   - Update API_BASE in Replit frontend
   - Run integration tests again

## 📚 Additional Resources

- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
- [Render.com Deployment Guide](https://render.com/docs)
- [Railway.app Docs](https://docs.railway.app/)
- [CORS Explained](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

## 🆘 Troubleshooting

### "CORS error" in browser console
- Check CORS configuration in `app.py`
- Verify Replit domain is in origins list
- Check backend is running and accessible

### "Connection refused" or "Network error"
- Verify backend is running
- Check API_BASE URL is correct
- For local testing, use `http://localhost:5000`
- For production, use your deployed backend URL

### "404 Not Found" on API calls
- Check endpoint path matches exactly
- Verify user/prescription IDs exist
- Check HTTP method (GET vs POST)

### Requests timing out
- Backend might be overloaded
- Database connection might be slow
- Check network connectivity

---

**Last Updated**: February 6, 2026
