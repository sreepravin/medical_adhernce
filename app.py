"""
Medication Adherence Support System - Flask Backend API
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import our modules
from db_connection import (
    get_db_connection, 
    close_db_connection, 
    execute_query, 
    execute_update
)
from medication_kb import (
    get_medication_info,
    create_plain_language_explanation,
    check_contraindications,
    get_adherence_nudge,
    format_daily_schedule
)
from ocr_processor import PrescriptionOCR, validate_prescription_input


def _create_reminder_for_dose(cursor, dose_tracking_id, user_id, scheduled_time, medicine_name, dosage=""):
    """Helper: create a reminder entry in the reminders table for a dose_tracking row.
    Reminder is set 15 minutes before the scheduled dose time."""
    try:
        reminder_time = scheduled_time - timedelta(minutes=15)
        reminder_text = f"Time to take {medicine_name}"
        if dosage:
            reminder_text += f" ({dosage})"
        cursor.execute("""
            INSERT INTO reminders
            (dose_tracking_id, user_id, reminder_text, reminder_time, is_sent, reminder_method)
            VALUES (%s, %s, %s, %s, FALSE, 'app')
        """, (dose_tracking_id, user_id, reminder_text, reminder_time))
    except Exception as e:
        print(f"Reminder creation note: {e}")

# Initialize Flask app
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

# Set max upload size to 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize OCR processor
ocr = PrescriptionOCR()

# ===== GLOBAL ERROR HANDLERS (always return JSON, never HTML) =====

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Endpoint not found", "error": str(e)}), 404
    # Non-API routes: serve frontend
    return send_from_directory('.', 'index.html')

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"status": "error", "message": "File too large. Maximum upload size is 16 MB.", "error": "Payload Too Large"}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status": "error", "message": "Internal server error", "error": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {str(e)}")
    return jsonify({"status": "error", "message": "An unexpected error occurred", "error": str(e)}), 500

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', None)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', None)

# ===== UTILITY FUNCTIONS =====

def success_response(data, message="Success", status_code=200):
    """Return standardized success response"""
    return jsonify({
        "status": "success",
        "message": message,
        "data": data
    }), status_code

def send_email(recipient_email, subject, body):
    """Send email via SMTP"""
    try:
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            print("⚠ Email not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")
        return False

def error_response(error, message="Error", status_code=400):
    """Return standardized error response"""
    return jsonify({
        "status": "error",
        "message": message,
        "error": error
    }), status_code

# ===== STEP 1: USER MANAGEMENT =====

@app.route('/api/users/login', methods=['POST'])
def login_user():
    """Login user with username and password"""
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        if not username or not password:
            return error_response("Username and password are required", "Validation Error", 400)
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed", "Database Error")
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("""
            SELECT id, username, email, full_name, password_hash, created_at 
            FROM users 
            WHERE username = %s
        """, (username,))
        
        user_result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not user_result:
            return error_response("Invalid username or password", "Authentication Error", 401)
        
        user_id, db_username, email, full_name, stored_password, created_at = user_result
        
        # Simple password comparison (in production, use bcrypt)
        if stored_password != password and stored_password is not None:
            return error_response("Invalid username or password", "Authentication Error", 401)
        
        user_data = {
            "id": user_id,
            "username": db_username,
            "email": email,
            "full_name": full_name,
            "created_at": created_at.isoformat() if created_at else None
        }
        
        return success_response(user_data, "Login successful", 200)
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return error_response(f"Login error: {str(e)}", "Server Error")

@app.route('/api/users/register', methods=['POST'])
def register_new_user():
    """Register a new user with password, DOB, and gender"""
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        email = data.get("email", "").strip()
        full_name = data.get("full_name", "")
        date_of_birth = data.get("date_of_birth")
        gender = data.get("gender", "")
        
        if not username or not password or not email:
            return error_response("Username, password, and email are required", "Validation Error", 400)
        
        if not full_name:
            return error_response("Full name is required", "Validation Error", 400)
        
        if not date_of_birth:
            return error_response("Date of birth is required", "Validation Error", 400)
        
        if not gender:
            return error_response("Gender is required", "Validation Error", 400)
        
        if len(password) < 4:
            return error_response("Password must be at least 4 characters", "Validation Error", 400)
        
        if len(username) < 3:
            return error_response("Username must be at least 3 characters", "Validation Error", 400)
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed", "Database Error")
        
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            close_db_connection(conn)
            return error_response("Username already exists", "Validation Error", 400)
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            close_db_connection(conn)
            return error_response("Email already registered", "Validation Error", 400)
        
        # Insert new user with password, DOB, and gender
        query = """
        INSERT INTO users (username, email, password_hash, full_name, date_of_birth, gender)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, username, email, full_name, date_of_birth, gender, created_at
        """
        
        cursor.execute(query, (username, email, password, full_name, date_of_birth, gender))
        conn.commit()
        
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        user_data = {
            "id": result[0],
            "username": result[1],
            "email": result[2],
            "full_name": result[3],
            "date_of_birth": result[4],
            "gender": result[5],
            "created_at": result[6].isoformat()
        }
        
        return success_response(user_data, "User registered successfully. Please login.", 201)
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return error_response(f"Registration error: {str(e)}", "Server Error")

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        query = "SELECT id, username, email, full_name, date_of_birth, gender, created_at FROM users WHERE id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return error_response("User not found", "Not Found", 404)
        
        user_data = {
            "id": result[0],
            "username": result[1],
            "email": result[2],
            "full_name": result[3],
            "date_of_birth": result[4].isoformat() if result[4] else None,
            "gender": result[5],
            "created_at": result[6].isoformat()
        }
        
        return success_response(user_data)
    
    except Exception as e:
        return error_response(str(e), "Error retrieving user")

@app.route('/api/users/<int:user_id>/medical-info', methods=['POST'])
def save_medical_info(user_id):
    """Save user's medical information (Step 6 - contraindication check setup)"""
    try:
        data = request.json
        conn = get_db_connection()
        
        if not conn:
            return error_response("Database connection failed")
        
        # Check if medical info exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_medical_info WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        
        drug_allergies = data.get("drug_allergies", "")
        food_allergies = data.get("food_allergies", "")
        existing_conditions = data.get("existing_conditions", "")
        current_medications = data.get("current_medications", "")
        is_pregnant = data.get("is_pregnant", False)
        is_breastfeeding = data.get("is_breastfeeding", False)

        if existing:
            cursor.execute("""
                UPDATE user_medical_info 
                SET drug_allergies = %s, food_allergies = %s, existing_conditions = %s,
                    current_medications = %s, is_pregnant = %s, is_breastfeeding = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (drug_allergies, food_allergies, existing_conditions,
                   current_medications, is_pregnant, is_breastfeeding, user_id))
        else:
            cursor.execute("""
                INSERT INTO user_medical_info 
                (user_id, drug_allergies, food_allergies, existing_conditions,
                 current_medications, is_pregnant, is_breastfeeding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, drug_allergies, food_allergies, existing_conditions,
                   current_medications, is_pregnant, is_breastfeeding))
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return success_response(
            {"user_id": user_id},
            "Medical information saved successfully"
        )
    
    except Exception as e:
        return error_response(str(e), "Error saving medical information")

@app.route('/api/users/<int:user_id>/medical-info', methods=['GET'])
def get_medical_info(user_id):
    """Get user's medical information"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        query = "SELECT * FROM user_medical_info WHERE user_id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return success_response({}, "No medical information on file")
        
        medical_data = {
            "id": result[0],
            "user_id": result[1],
            "drug_allergies": result[2],
            "food_allergies": result[3],
            "existing_conditions": result[4],
            "current_medications": result[5],
            "is_pregnant": result[6],
            "is_breastfeeding": result[7],
        }
        
        return success_response(medical_data)
    
    except Exception as e:
        return error_response(str(e), "Error retrieving medical information")

# ===== GEMINI AI CONFIG =====

@app.route('/api/gemini/status', methods=['GET'])
def gemini_status():
    """Check if Gemini AI is configured and available"""
    return success_response({
        "gemini_available": ocr.gemini_available,
        "tesseract_available": ocr.tesseract_available,
        "api_key_set": bool(os.environ.get('GEMINI_API_KEY', '')),
    })

@app.route('/api/gemini/set-key', methods=['POST'])
def set_gemini_key():
    """Set the Gemini API key at runtime"""
    try:
        data = request.json
        api_key = data.get('api_key', '').strip()
        if not api_key:
            return error_response("API key is required", "Validation Error", 400)
        
        # Set in environment
        os.environ['GEMINI_API_KEY'] = api_key
        
        # Re-initialize Gemini in the OCR processor
        try:
            from google import genai
            ocr.gemini_client = genai.Client(api_key=api_key)
            ocr.gemini_available = True
            
            # Also save to .env file for persistence
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            env_lines = []
            key_found = False
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
                for i, line in enumerate(env_lines):
                    if line.strip().startswith('GEMINI_API_KEY'):
                        env_lines[i] = f'GEMINI_API_KEY={api_key}\n'
                        key_found = True
                        break
            if not key_found:
                env_lines.append(f'\n# Google Gemini AI Key\nGEMINI_API_KEY={api_key}\n')
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            return success_response({"gemini_available": True}, "Gemini AI configured successfully! You can now use AI-powered prescription scanning.")
        except Exception as e:
            return error_response(f"Failed to initialize Gemini: {str(e)}", "Configuration Error")
    except Exception as e:
        return error_response(str(e), "Error setting API key")

# ===== STEPS 2-3: PRESCRIPTION INPUT & PROCESSING =====

@app.route('/api/prescriptions/ocr', methods=['POST', 'OPTIONS'])
def process_prescription_image():
    """Process prescription image via OCR and save ALL medicines to database"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200
    
    try:
        if 'image' not in request.files:
            return error_response("No image provided", "Validation Error", 400)
        
        image_file = request.files['image']
        
        # Check file size early (max 10 MB for images)
        image_file.seek(0, 2)  # Seek to end
        file_size = image_file.tell()
        image_file.seek(0)  # Reset
        if file_size > 10 * 1024 * 1024:
            return error_response("Image too large. Please use an image under 10 MB.", "Validation Error", 400)
        if file_size == 0:
            return error_response("Empty image file", "Validation Error", 400)
        user_id = request.form.get('user_id')
        username = request.form.get('username', f'user_{user_id}')
        save_to_db = request.form.get('save_to_db', 'true').lower() == 'true'
        
        if not user_id:
            return error_response("user_id required", "Validation Error", 400)
        
        # Process OCR — now returns a LIST of prescription dicts
        image_bytes = image_file.read()
        image_file.close()  # Free file handle
        prescription_list = ocr.extract_from_image(image_bytes)
        del image_bytes  # Free memory immediately
        
        # Handle legacy single-dict return (shouldn't happen but be safe)
        if isinstance(prescription_list, dict):
            prescription_list = [prescription_list]
        
        if not prescription_list or len(prescription_list) == 0:
            return error_response("Could not extract any data from image", "OCR Error")
        
        # Check if first entry has an error
        if prescription_list[0].get("error"):
            err_msg = prescription_list[0].get("error", "OCR processing failed")
            print(f"[OCR API] Returning error to client: {err_msg}")
            prescription_list[0]["requires_manual_confirmation"] = True
            return success_response(
                {"medicines": prescription_list, "count": 0},
                err_msg
            )
        
        # Log successful extraction
        med_names = [rx.get('medicine_name', '?') for rx in prescription_list]
        print(f"[OCR API] Extracted {len(prescription_list)} medicines: {', '.join(med_names)}")
        
        # Tag each medicine with user info
        for rx in prescription_list:
            rx["user_id"] = int(user_id)
            rx["username"] = username
        
        # Auto-save ALL medicines to database if requested
        if save_to_db:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Ensure user exists
                try:
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO users (id, username, email, password_hash)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (user_id, username, f"{username}@demo.local", "demo"))
                        conn.commit()
                except Exception as e:
                    print(f"User check note: {e}")
                
                for rx in prescription_list:
                    if not rx.get("medicine_name"):
                        continue
                    
                    start_date = datetime.now().date()
                    duration_val = rx.get("duration") or 30
                    end_date = (start_date + timedelta(days=int(duration_val))).isoformat()
                    
                    # Look up instructions from medication KB
                    med_info = get_medication_info(rx.get("medicine_name", ""))
                    instructions = None
                    special_instructions = None
                    if med_info:
                        instructions = f"{med_info.get('how_to_take', '')}. {med_info.get('with_food', '')}. {med_info.get('duration_instruction', '')}".strip('. ')
                        special_instructions = f"Contraindications: {', '.join(med_info.get('contraindications', []))}. {med_info.get('risks_of_skipping', '')}".strip('. ')
                    
                    try:
                        query = """
                        INSERT INTO prescriptions 
                        (user_id, medication_id, medicine_name, dosage, dosage_unit, frequency, duration,
                         start_date, end_date, route, instructions, special_instructions,
                         prescription_image_url, ocr_confidence, is_confirmed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """
                        
                        cursor.execute(query, (
                            user_id,
                            None,
                            rx.get("medicine_name"),
                            rx.get("dosage"),
                            rx.get("dosage_unit", "mg"),
                            rx.get("frequency", "Once daily"),
                            duration_val,
                            start_date,
                            end_date,
                            rx.get("route", "oral"),
                            instructions or rx.get("instructions"),
                            special_instructions or rx.get("special_instructions"),
                            f"ocr_upload_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            rx.get("ocr_confidence", 0.5),
                            False
                        ))
                        
                        prescription_id = cursor.fetchone()[0]
                        conn.commit()
                        rx["prescription_id"] = prescription_id
                        rx["saved"] = True
                        rx["instructions"] = instructions or rx.get("instructions")
                        rx["special_instructions"] = special_instructions or rx.get("special_instructions")
                        
                        # Auto-create adherence plan & dose tracking
                        try:
                            frequency = rx.get("frequency", "Once daily")
                            daily_schedule = format_daily_schedule("1", frequency)
                            nudges = get_adherence_nudge(rx.get("medicine_name", ""), frequency)
                            why_important = med_info.get("why_important") if med_info else "Follow your medication schedule."
                            nudge_reason = nudges[0].get("message") if nudges else "Taking medication as prescribed is important."
                            
                            cursor.execute("""
                                INSERT INTO adherence_plans
                                (prescription_id, user_id, daily_schedule, why_important, nudge_reason)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                            """, (prescription_id, user_id, daily_schedule, why_important, nudge_reason))
                            plan_id = cursor.fetchone()[0]
                            conn.commit()
                            
                            medicine_name_ocr = rx.get('medicine_name', 'Medication')
                            dosage_ocr = f"{rx.get('dosage', '')} {rx.get('dosage_unit', 'mg')}".strip()
                            for day in range(int(duration_val)):
                                current_date = start_date + timedelta(days=day)
                                for time_str in daily_schedule:
                                    hour, minute = map(int, time_str.split(':'))
                                    scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                                    cursor.execute("""
                                        INSERT INTO dose_tracking
                                        (adherence_plan_id, prescription_id, user_id, scheduled_time)
                                        VALUES (%s, %s, %s, %s)
                                        RETURNING id
                                    """, (plan_id, prescription_id, user_id, scheduled_time))
                                    dt_id = cursor.fetchone()[0]
                                    _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, medicine_name_ocr, dosage_ocr)
                            conn.commit()
                        except Exception as plan_err:
                            print(f"Adherence plan creation note for {rx.get('medicine_name')}: {plan_err}")
                    except Exception as save_err:
                        print(f"Error saving {rx.get('medicine_name')}: {save_err}")
                        rx["saved"] = False
                        rx["save_error"] = str(save_err)
                
                cursor.close()
                close_db_connection(conn)
        
        count = len(prescription_list)
        saved_count = sum(1 for rx in prescription_list if rx.get("saved"))
        msg = f"Found {count} medicine(s) in prescription"
        if save_to_db:
            msg += f", saved {saved_count} to database"
        
        return success_response(
            {"medicines": prescription_list, "count": count},
            msg
        )
    
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return error_response(str(e), "OCR Processing Error")

@app.route('/api/prescriptions/manual-entry', methods=['POST'])
def manual_prescription_entry():
    """Manual prescription entry (Step 2)"""
    try:
        data = request.json
        user_id = data.get("user_id")
        
        if not user_id:
            return error_response("user_id required", "Validation Error", 400)
        
        prescription_data = {
            "user_id": user_id,
            "medicine_name": data.get("medicine_name"),
            "dosage": data.get("dosage"),
            "dosage_unit": data.get("dosage_unit", "mg"),
            "frequency": data.get("frequency"),
            "duration": data.get("duration"),
            "route": data.get("route", "oral"),
            "instructions": data.get("instructions"),
            "prescribed_by": data.get("prescribed_by")
        }
        
        # Validate
        errors = validate_prescription_input(prescription_data)
        if errors:
            return error_response(errors, "Validation Error", 400)
        
        return success_response(prescription_data, "Prescription data validated")
    
    except Exception as e:
        return error_response(str(e), "Validation Error")

@app.route('/api/prescriptions', methods=['POST'])
def save_prescription():
    """Save prescription to database (Step 3 & 4)"""
    try:
        data = request.json
        user_id = data.get("user_id")
        username = data.get("username", f"user_{user_id}")
        conn = get_db_connection()
        
        if not conn:
            return error_response("Database connection failed")
        
        # Validate
        errors = validate_prescription_input(data)
        if errors:
            return error_response(errors, "Validation Error", 400)
        
        cursor = conn.cursor()
        
        # Step 1: Create user if doesn't exist (for demo mode)
        try:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (user_id, username, f"{username}@demo.local", "demo"))
                conn.commit()
        except Exception as e:
            print(f"User creation note: {e}")
        
        # Step 2: Insert prescription
        query = """
        INSERT INTO prescriptions 
        (user_id, medication_id, medicine_name, dosage, dosage_unit, frequency, duration,
         start_date, end_date, route, instructions, special_instructions, prescribed_by, 
         prescription_image_url, ocr_confidence, is_confirmed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        start_date = data.get("start_date") or datetime.now().date()
        
        # Calculate end_date from start_date + duration if not provided
        end_date = data.get("end_date")
        if not end_date and data.get("duration"):
            from datetime import timedelta
            if isinstance(start_date, str):
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                sd = start_date
            end_date = (sd + timedelta(days=int(data.get("duration")))).isoformat()
        
        cursor.execute(query, (
            user_id,
            data.get("medication_id"),
            data.get("medicine_name"),
            data.get("dosage"),
            data.get("dosage_unit", "mg"),
            data.get("frequency"),
            data.get("duration"),
            start_date,
            end_date,
            data.get("route", "oral"),
            data.get("instructions"),
            data.get("special_instructions"),
            data.get("prescribed_by"),
            data.get("prescription_image_url"),
            data.get("ocr_confidence", 1.0),
            data.get("is_confirmed", False)
        ))
        
        prescription_id = cursor.fetchone()[0]
        conn.commit()
        
        # ===== AUTO-CREATE ADHERENCE PLAN & DOSE TRACKING =====
        try:
            medicine_name = data.get("medicine_name")
            frequency = data.get("frequency", "Once daily")
            duration_days = int(data.get("duration") or 30)
            
            daily_schedule = format_daily_schedule("1", frequency)
            med_info = get_medication_info(medicine_name)
            nudges = get_adherence_nudge(medicine_name, frequency)
            
            why_important = med_info.get("why_important") if med_info else "Follow this medication schedule to maintain your health."
            nudge_reason = nudges[0].get("message") if nudges else "Taking your medication as prescribed is important."
            
            # Create adherence plan
            cursor.execute("""
                INSERT INTO adherence_plans 
                (prescription_id, user_id, daily_schedule, why_important, nudge_reason)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (prescription_id, user_id, daily_schedule, why_important, nudge_reason))
            
            plan_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✓ Created adherence plan {plan_id}")
            
            # Create dose tracking entries
            if isinstance(start_date, str):
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                sd = start_date
            
            dose_count = 0
            med_name = data.get("medicine_name", "Medication")
            med_dosage = f"{data.get('dosage', '')} {data.get('dosage_unit', 'mg')}".strip()
            for day in range(duration_days):
                current_date = sd + timedelta(days=day)
                for time_str in daily_schedule:
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                    cursor.execute("""
                        INSERT INTO dose_tracking 
                        (adherence_plan_id, prescription_id, user_id, scheduled_time)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (plan_id, prescription_id, user_id, scheduled_time))
                    dt_id = cursor.fetchone()[0]
                    _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, med_name, med_dosage)
                    dose_count += 1
            
            conn.commit()
            print(f"✓ Created {dose_count} dose tracking + reminder entries for prescription {prescription_id}")
            
        except Exception as plan_err:
            try:
                conn.rollback()
            except:
                pass
            print(f"✗ Error creating adherence plan: {plan_err}")
            import traceback
            traceback.print_exc()
        
        close_db_connection(conn)
        
        return success_response(
            {"prescription_id": prescription_id},
            "Prescription saved successfully",
            201
        )
    
    except Exception as e:
        print(f"Error in save_prescription: {str(e)}")
        return error_response(f"Error saving prescription: {str(e)}", "Database Error")

@app.route('/api/prescriptions/user/<int:user_id>/init-tracking', methods=['POST'])
def init_dose_tracking_for_user(user_id):
    """Create dose tracking for all prescriptions that don't have tracking yet"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")

        cursor = conn.cursor()
        
        # Find prescriptions without adherence plans
        cursor.execute("""
            SELECT p.id, p.medicine_name, p.frequency, p.duration, p.start_date
            FROM prescriptions p
            LEFT JOIN adherence_plans ap ON ap.prescription_id = p.id
            WHERE p.user_id = %s AND ap.id IS NULL
        """, (user_id,))
        prescriptions_without_plans = cursor.fetchall()
        
        # Find prescriptions with plans but WITHOUT dose tracking
        cursor.execute("""
            SELECT p.id, ap.id, p.medicine_name, p.frequency, p.duration, p.start_date
            FROM prescriptions p
            JOIN adherence_plans ap ON ap.prescription_id = p.id
            LEFT JOIN dose_tracking dt ON dt.adherence_plan_id = ap.id
            WHERE p.user_id = %s AND dt.id IS NULL
        """, (user_id,))
        prescriptions_without_tracking = cursor.fetchall()

        created_count = 0
        dose_count = 0

        # Create adherence plans for prescriptions without them
        for presc_id, medicine_name, frequency, duration_days, start_date in prescriptions_without_plans:
            try:
                frequency = frequency or "Once daily"
                duration_days = duration_days or 30
                daily_schedule = format_daily_schedule("1", frequency)
                med_info = get_medication_info(medicine_name)
                nudges = get_adherence_nudge(medicine_name, frequency)

                why_important = med_info.get("why_important") if med_info else "Follow your medication schedule."
                nudge_reason = nudges[0].get("message") if nudges else "Taking your medication as prescribed is important."

                cursor.execute("""
                    INSERT INTO adherence_plans
                    (prescription_id, user_id, daily_schedule, why_important, nudge_reason)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (presc_id, user_id, daily_schedule, why_important, nudge_reason))
                plan_id = cursor.fetchone()[0]
                conn.commit()
                print(f"✓ Created adherence plan {plan_id} for prescription {presc_id}")
                created_count += 1

                # Create dose tracking + reminders for this new plan
                sd = start_date if start_date else datetime.now().date()
                for day in range(duration_days):
                    current_date = sd + timedelta(days=day)
                    for time_str in daily_schedule:
                        hour, minute = map(int, time_str.split(':'))
                        scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                        cursor.execute("""
                            INSERT INTO dose_tracking
                            (adherence_plan_id, prescription_id, user_id, scheduled_time)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (plan_id, presc_id, user_id, scheduled_time))
                        dt_id = cursor.fetchone()[0]
                        _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, medicine_name)
                        dose_count += 1
                conn.commit()
                print(f"✓ Created {duration_days * len(daily_schedule)} dose + reminder entries for plan {plan_id}")
            except Exception as e:
                print(f"Error processing prescription {presc_id}: {e}")
                try:
                    conn.rollback()
                except:
                    pass

        # Create dose tracking + reminders for prescriptions with plans but no tracking
        for presc_id, plan_id, medicine_name, frequency, duration_days, start_date in prescriptions_without_tracking:
            try:
                frequency = frequency or "Once daily"
                duration_days = duration_days or 30
                daily_schedule = format_daily_schedule("1", frequency)

                sd = start_date if start_date else datetime.now().date()
                for day in range(duration_days):
                    current_date = sd + timedelta(days=day)
                    for time_str in daily_schedule:
                        hour, minute = map(int, time_str.split(':'))
                        scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                        cursor.execute("""
                            INSERT INTO dose_tracking
                            (adherence_plan_id, prescription_id, user_id, scheduled_time)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (plan_id, presc_id, user_id, scheduled_time))
                        dt_id = cursor.fetchone()[0]
                        _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, medicine_name)
                        dose_count += 1
                conn.commit()
                print(f"✓ Created {duration_days * len(daily_schedule)} dose + reminder entries for prescription {presc_id}")
            except Exception as e:
                print(f"Error creating dose tracking for prescription {presc_id}: {e}")
                try:
                    conn.rollback()
                except:
                    pass

        cursor.close()
        close_db_connection(conn)

        return success_response({
            "initialized": created_count,
            "dose_entries_created": dose_count,
            "message": f"Dose tracking initialized for {created_count} prescriptions with {dose_count} dose entries"
        })

    except Exception as e:
        print(f"Error initializing dose tracking: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(str(e), "Error")

@app.route('/api/prescriptions/rebuild-tracking', methods=['POST'])
def rebuild_all_tracking():
    """Rebuild dose tracking for all prescriptions (admin function for fixing issues)"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")

        cursor = conn.cursor()
        
        # Get all users with prescriptions
        cursor.execute("""
            SELECT DISTINCT user_id FROM prescriptions
        """)
        users = cursor.fetchall()

        total_initialized = 0
        total_doses = 0

        for (user_id,) in users:
            # Call init for each user
            cursor.execute("""
                SELECT p.id, p.medicine_name, p.frequency, p.duration, p.start_date
                FROM prescriptions p
                LEFT JOIN adherence_plans ap ON ap.prescription_id = p.id
                WHERE p.user_id = %s AND ap.id IS NULL
            """, (user_id,))
            prescriptions = cursor.fetchall()

            for presc_id, medicine_name, frequency, duration_days, start_date in prescriptions:
                try:
                    frequency = frequency or "Once daily"
                    duration_days = duration_days or 30
                    daily_schedule = format_daily_schedule("1", medicine_name)
                    
                    cursor.execute("""
                        INSERT INTO adherence_plans
                        (prescription_id, user_id, daily_schedule, why_important, nudge_reason)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (presc_id, user_id, daily_schedule, "Follow your medication schedule", "Important for health"))
                    plan_id = cursor.fetchone()[0]
                    conn.commit()
                    total_initialized += 1

                    sd = start_date if start_date else datetime.now().date()
                    for day in range(duration_days):
                        current_date = sd + timedelta(days=day)
                        for time_str in daily_schedule:
                            hour, minute = map(int, time_str.split(':'))
                            scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                            cursor.execute("""
                                INSERT INTO dose_tracking
                                (adherence_plan_id, prescription_id, user_id, scheduled_time)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, (plan_id, presc_id, user_id, scheduled_time))
                            dt_id = cursor.fetchone()[0]
                            _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, medicine_name)
                            total_doses += 1
                    conn.commit()
                except Exception as e:
                    print(f"Error: {e}")
                    try:
                        conn.rollback()
                    except:
                        pass

        cursor.close()
        close_db_connection(conn)

        return success_response({
            "prescriptions_fixed": total_initialized,
            "total_doses_created": total_doses,
            "message": f"Rebuilt tracking for {total_initialized} prescriptions with {total_doses} reminders"
        })

    except Exception as e:
        print(f"Error rebuilding tracking: {str(e)}")
        return error_response(str(e), "Error")

@app.route('/api/prescriptions/user/<int:user_id>', methods=['GET'])
def get_user_prescriptions(user_id):
    """Get all prescriptions for a user"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, medication_id, medicine_name, dosage, dosage_unit, frequency, duration,
                   start_date, end_date, route, instructions, special_instructions, 
                   prescribed_by, prescription_image_url, is_confirmed, created_at
            FROM prescriptions 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)

        prescriptions = []
        for r in rows:
            prescriptions.append({
                "id": r[0],
                "medication_id": r[1],
                "medicine_name": r[2],
                "dosage": r[3],
                "dosage_unit": r[4],
                "frequency": r[5],
                "duration": r[6],
                "start_date": r[7].isoformat() if r[7] else None,
                "end_date": r[8].isoformat() if r[8] else None,
                "route": r[9],
                "instructions": r[10],
                "special_instructions": r[11],
                "prescribed_by": r[12],
                "prescription_image_url": r[13],
                "is_confirmed": r[14],
                "created_at": r[15].isoformat() if r[15] else None
            })

        return success_response({
            "prescriptions": prescriptions,
            "total": len(prescriptions)
        })

    except Exception as e:
        print(f"Error fetching prescriptions: {str(e)}")
        return error_response(f"Error fetching prescriptions: {str(e)}", "Database Error")

# ===== STEP 4: MEDICATION UNDERSTANDING =====

@app.route('/api/medications/<medicine_name>', methods=['GET'])
def get_medication_understanding(medicine_name):
    """Get plain language medication explanation (Step 4)"""
    try:
        med_info = get_medication_info(medicine_name)
        
        if not med_info:
            return error_response(
                f"Medication '{medicine_name}' not found in database",
                "Not Found",
                404
            )
        
        explanation = create_plain_language_explanation(med_info)
        
        return success_response({
            "medicine_name": medicine_name,
            "generic_name": med_info.get("generic_name"),
            "what_for": med_info.get("what_for"),
            "how_works": med_info.get("how_works"),
            "how_to_take": med_info.get("how_to_take"),
            "with_food": med_info.get("with_food"),
            "side_effects": med_info.get("side_effects"),
            "instructions": f"{med_info.get('how_to_take', '')}. {med_info.get('with_food', '')}. {med_info.get('duration_instruction', '')}".strip('. '),
            "special_instructions": f"Contraindications: {', '.join(med_info.get('contraindications', []))}. {med_info.get('risks_of_skipping', '')}".strip('. '),
            "plain_language_explanation": explanation
        })
    
    except Exception as e:
        return error_response(str(e), "Error retrieving medication information")

# ===== STEPS 5 & 6: ADHERENCE NUDGES & CONTRAINDICATION CHECK =====

@app.route('/api/adherence/nudges/<int:prescription_id>', methods=['GET'])
def get_adherence_nudges(prescription_id):
    """Get behavioral nudges for adherence (Step 5)"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        query = "SELECT medicine_name, frequency FROM prescriptions WHERE id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (prescription_id,))
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return error_response("Prescription not found", "Not Found", 404)
        
        medicine_name, frequency = result
        nudges = get_adherence_nudge(medicine_name, frequency)
        
        return success_response({
            "prescription_id": prescription_id,
            "medicine_name": medicine_name,
            "nudges": nudges
        })
    
    except Exception as e:
        return error_response(str(e), "Error retrieving nudges")

@app.route('/api/contraindications', methods=['POST'])
def check_drug_contraindications():
    """Check for drug contraindications (Step 6)"""
    try:
        data = request.json
        user_id = data.get("user_id")
        medicine_name = data.get("medicine_name")
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get user's medical info
        query = "SELECT * FROM user_medical_info WHERE user_id = %s"
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        med_info_result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        # Create medical info dict
        user_medical_info = {}
        if med_info_result:
            user_medical_info = {
                "drug_allergies": med_info_result[2],
                "food_allergies": med_info_result[3],
                "existing_conditions": med_info_result[4],
                "current_medications": med_info_result[5],
                "is_pregnant": med_info_result[6],
                "is_breastfeeding": med_info_result[7],
            }
        
        # Check contraindications
        warnings = check_contraindications(medicine_name, user_medical_info)
        
        return success_response({
            "medicine_name": medicine_name,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0,
            "requires_confirmation": any(w["risk"] in ["HIGH", "MEDIUM"] for w in warnings)
        })
    
    except Exception as e:
        return error_response(str(e), "Error checking contraindications")

# ===== STEP 7: PERSONALIZED ADHERENCE PLAN =====

@app.route('/api/adherence-plans', methods=['POST'])
def create_adherence_plan():
    """Create personalized adherence plan (Step 7)"""
    try:
        data = request.json
        prescription_id = data.get("prescription_id")
        user_id = data.get("user_id")
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get prescription details
        cursor = conn.cursor()
        cursor.execute(
            "SELECT medicine_name, frequency, duration FROM prescriptions WHERE id = %s",
            (prescription_id,)
        )
        presc_result = cursor.fetchone()
        
        if not presc_result:
            cursor.close()
            close_db_connection(conn)
            return error_response("Prescription not found", "Not Found", 404)
        
        medicine_name, frequency, duration = presc_result
        
        # Generate schedule
        daily_schedule = format_daily_schedule("1", frequency)
        med_info = get_medication_info(medicine_name)
        nudges = get_adherence_nudge(medicine_name, frequency)
        
        why_important = med_info.get("why_important") if med_info else "Follow this medication schedule to maintain your health."
        nudge_reason = nudges[0].get("message") if nudges else "Taking your medication as prescribed is important for your health."
        
        # Save adherence plan
        query = """
        INSERT INTO adherence_plans 
        (prescription_id, user_id, daily_schedule, why_important, nudge_reason)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, created_at
        """
        
        cursor.execute(query, (
            prescription_id,
            user_id,
            daily_schedule,
            why_important,
            nudge_reason
        ))
        
        plan_id, created_at = cursor.fetchone()
        conn.commit()
        
        # Create dose tracking entries for the prescription period
        start_date = datetime.now().date()
        duration_days = duration if duration else 30
        
        for day in range(duration_days):
            current_date = start_date + timedelta(days=day)
            
            for time_str in daily_schedule:
                hour, minute = map(int, time_str.split(':'))
                scheduled_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                
                cursor.execute(
                    """
                    INSERT INTO dose_tracking 
                    (adherence_plan_id, prescription_id, user_id, scheduled_time)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (plan_id, prescription_id, user_id, scheduled_time)
                )
                dt_id = cursor.fetchone()[0]
                _create_reminder_for_dose(cursor, dt_id, user_id, scheduled_time, medicine_name)
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return success_response({
            "plan_id": plan_id,
            "prescription_id": prescription_id,
            "daily_schedule": daily_schedule,
            "why_important": why_important,
            "nudges": nudges,
            "created_at": created_at.isoformat()
        }, "Adherence plan created successfully", 201)
    
    except Exception as e:
        return error_response(str(e), "Error creating adherence plan")

@app.route('/api/adherence-plans/<int:plan_id>', methods=['GET'])
def get_adherence_plan(plan_id):
    """Get adherence plan details"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        query = """
        SELECT id, prescription_id, user_id, daily_schedule, why_important, 
               nudge_reason, completion_percentage, created_at
        FROM adherence_plans WHERE id = %s
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (plan_id,))
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return error_response("Plan not found", "Not Found", 404)
        
        plan_data = {
            "id": result[0],
            "prescription_id": result[1],
            "user_id": result[2],
            "daily_schedule": result[3],
            "why_important": result[4],
            "nudge_reason": result[5],
            "completion_percentage": result[6],
            "created_at": result[7].isoformat()
        }
        
        return success_response(plan_data)
    
    except Exception as e:
        return error_response(str(e), "Error retrieving adherence plan")

# ===== HEALTHCARE PROVIDERS =====

@app.route('/api/healthcare-providers/<int:user_id>', methods=['GET'])
def get_healthcare_providers(user_id):
    """Get healthcare providers for a user"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, provider_name, provider_type, contact_email, contact_phone, 
                   specialization, created_at
            FROM healthcare_providers
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        
        providers = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        providers_list = [
            {
                "id": p[0],
                "provider_name": p[1],
                "provider_type": p[2],
                "contact_email": p[3],
                "contact_phone": p[4],
                "specialization": p[5],
                "created_at": p[6].isoformat() if p[6] else None
            }
            for p in providers
        ]
        
        return success_response(providers_list, f"Found {len(providers_list)} healthcare provider(s)")
    
    except Exception as e:
        return error_response(str(e), "Error retrieving healthcare providers")

# ===== STEPS 8 & 9: REMINDER SYSTEM & MISSED DOSE HANDLING =====

@app.route('/api/reminders/upcoming/<int:user_id>', methods=['GET'])
def get_upcoming_reminders(user_id):
    """Get upcoming reminders for user — reads from the reminders table joined with dose_tracking"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get today's reminders from the reminders table joined with dose_tracking & prescriptions
        query = """
        SELECT dt.id AS dose_id, dt.scheduled_time, dt.status,
               pr.medicine_name, pr.dosage, pr.dosage_unit,
               r.id AS reminder_id, r.reminder_text, r.reminder_time,
               r.is_sent, r.sent_at, r.reminder_method
        FROM dose_tracking dt
        JOIN prescriptions pr ON dt.prescription_id = pr.id
        LEFT JOIN reminders r ON r.dose_tracking_id = dt.id
        WHERE dt.user_id = %s AND DATE(dt.scheduled_time) = CURRENT_DATE
        ORDER BY dt.scheduled_time
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        reminders = []
        for result in results:
            reminders.append({
                "dose_id": result[0],
                "scheduled_time": result[1].isoformat(),
                "status": result[2],
                "medicine_name": result[3],
                "dosage": f"{result[4]} {result[5]}",
                "reminder_id": result[6],
                "reminder_text": result[7] or f"Time to take {result[3]}",
                "reminder_time": result[8].isoformat() if result[8] else None,
                "is_sent": result[9] if result[9] is not None else False,
                "sent_at": result[10].isoformat() if result[10] else None,
                "reminder_method": result[11] or "app"
            })
        
        return success_response({
            "user_id": user_id,
            "upcoming_reminders": reminders,
            "count": len(reminders)
        })
    
    except Exception as e:
        return error_response(str(e), "Error retrieving reminders")


@app.route('/api/reminders/all/<int:user_id>', methods=['GET'])
def get_all_reminders(user_id):
    """Get all reminders for user — full history from the reminders table"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.reminder_text, r.reminder_time, r.is_sent, r.sent_at,
                   r.reminder_method, r.created_at,
                   dt.scheduled_time, dt.status AS dose_status,
                   pr.medicine_name, pr.dosage, pr.dosage_unit
            FROM reminders r
            JOIN dose_tracking dt ON r.dose_tracking_id = dt.id
            JOIN prescriptions pr ON dt.prescription_id = pr.id
            WHERE r.user_id = %s
            ORDER BY r.reminder_time DESC
            LIMIT 100
        """, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        reminder_list = []
        for row in results:
            reminder_list.append({
                "reminder_id": row[0],
                "reminder_text": row[1],
                "reminder_time": row[2].isoformat() if row[2] else None,
                "is_sent": row[3],
                "sent_at": row[4].isoformat() if row[4] else None,
                "reminder_method": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "scheduled_time": row[7].isoformat() if row[7] else None,
                "dose_status": row[8],
                "medicine_name": row[9],
                "dosage": f"{row[10]} {row[11]}"
            })
        
        return success_response({
            "user_id": user_id,
            "reminders": reminder_list,
            "count": len(reminder_list)
        })
    
    except Exception as e:
        return error_response(str(e), "Error retrieving all reminders")


@app.route('/api/reminders/<int:reminder_id>/mark-sent', methods=['POST'])
def mark_reminder_sent(reminder_id):
    """Mark a reminder as sent"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reminders 
            SET is_sent = TRUE, sent_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, is_sent, sent_at
        """, (reminder_id,))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return error_response("Reminder not found", "Not Found", 404)
        
        return success_response({
            "reminder_id": result[0],
            "is_sent": result[1],
            "sent_at": result[2].isoformat()
        }, "Reminder marked as sent")
    
    except Exception as e:
        return error_response(str(e), "Error updating reminder")


@app.route('/api/reminders/<int:reminder_id>/update-method', methods=['PUT'])
def update_reminder_method(reminder_id):
    """Update reminder delivery method (app, email, sms)"""
    try:
        data = request.json or {}
        method = data.get("reminder_method", "app")
        
        if method not in ("app", "email", "sms"):
            return error_response("Invalid method. Use 'app', 'email', or 'sms'", "Validation Error", 400)
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reminders SET reminder_method = %s WHERE id = %s
            RETURNING id, reminder_method
        """, (method, reminder_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        if not result:
            return error_response("Reminder not found", "Not Found", 404)
        
        return success_response({
            "reminder_id": result[0],
            "reminder_method": result[1]
        }, "Reminder method updated")
    
    except Exception as e:
        return error_response(str(e), "Error updating reminder method")


@app.route('/api/reminders/populate/<int:user_id>', methods=['POST'])
def populate_reminders_for_existing(user_id):
    """Populate reminders table for existing dose_tracking entries that don't have reminders yet"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dt.id, dt.scheduled_time, pr.medicine_name, pr.dosage, pr.dosage_unit
            FROM dose_tracking dt
            JOIN prescriptions pr ON dt.prescription_id = pr.id
            LEFT JOIN reminders r ON r.dose_tracking_id = dt.id
            WHERE dt.user_id = %s AND r.id IS NULL
        """, (user_id,))
        missing = cursor.fetchall()
        
        count = 0
        for dt_id, sched_time, med_name, dosage, dosage_unit in missing:
            dosage_str = f"{dosage} {dosage_unit}".strip() if dosage else ""
            _create_reminder_for_dose(cursor, dt_id, user_id, sched_time, med_name, dosage_str)
            count += 1
        
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return success_response({
            "reminders_created": count,
            "message": f"Created {count} reminders for existing doses"
        })
    
    except Exception as e:
        return error_response(str(e), "Error populating reminders")

@app.route('/api/doses/<int:dose_id>/mark-taken', methods=['POST'])
def mark_dose_taken(dose_id):
    """Mark dose as taken"""
    try:
        data = request.json or {}
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        note = data.get("notes", "Taken by user")
        
        query = """
        UPDATE dose_tracking 
        SET status = 'taken', actual_time = CURRENT_TIMESTAMP, notes = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id, status, actual_time, notes
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (note, dose_id))
        conn.commit()
        
        result = cursor.fetchone()
        cursor.close()
        close_db_connection(conn)
        
        return success_response({
            "dose_id": result[0],
            "status": result[1],
            "actual_time": result[2].isoformat(),
            "notes": result[3]
        }, "Dose marked as taken")
    
    except Exception as e:
        return error_response(str(e), "Error marking dose")

@app.route('/api/doses/<int:dose_id>/mark-missed', methods=['POST'])
def mark_dose_missed(dose_id):
    """Mark dose as missed and provide guidance (Step 9)"""
    try:
        data = request.json
        conn = get_db_connection()
        
        if not conn:
            return error_response("Database connection failed")
        
        cursor = conn.cursor()
        
        # Get dose details
        cursor.execute(
            "SELECT scheduled_time, prescription_id FROM dose_tracking WHERE id = %s",
            (dose_id,)
        )
        dose_result = cursor.fetchone()
        
        if not dose_result:
            cursor.close()
            close_db_connection(conn)
            return error_response("Dose not found", "Not Found", 404)
        
        scheduled_time, prescription_id = dose_result
        
        # Calculate time difference
        time_diff = (datetime.now() - scheduled_time).total_seconds() / 3600
        
        # Provide guidance
        guidance = {
            "should_take": True,
            "message": "It's not too late - take your dose now!",
            "warning": None
        }
        
        if time_diff > 24:
            guidance["should_take"] = False
            guidance["message"] = "This dose was missed more than 24 hours ago."
            guidance["warning"] = "IMPORTANT: Never double dose. Take your next regular dose at the scheduled time."
        elif time_diff > 12:
            guidance["should_take"] = True
            guidance["message"] = "You can still take this dose, but make sure to take your next dose at the regular time."
            guidance["warning"] = "Do NOT double dose."
        
        # Mark as missed
        query = """
        UPDATE dose_tracking 
        SET status = 'missed', actual_time = CURRENT_TIMESTAMP, notes = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        cursor.execute(query, (data.get("reason", "User reported as missed"), dose_id))
        conn.commit()
        cursor.close()
        close_db_connection(conn)
        
        return success_response({
            "dose_id": dose_id,
            "time_since_scheduled_hours": round(time_diff, 1),
            "guidance": guidance
        }, "Dose marked as missed with guidance provided")
    
    except Exception as e:
        return error_response(str(e), "Error processing missed dose")

# ===== STEP 10: MONITORING & FEEDBACK LOOP =====

@app.route('/api/adherence-summary/<int:user_id>', methods=['GET'])
def get_adherence_summary(user_id):
    """Get adherence summary for user (Step 10)"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get today's summary
        query = """
        SELECT SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as doses_taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as doses_missed,
               COUNT(*) as total_doses
        FROM dose_tracking 
        WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        doses_taken = result[0] or 0
        doses_missed = result[1] or 0
        total_doses = result[2] or 0
        
        adherence_percentage = (doses_taken / total_doses * 100) if total_doses > 0 else 0
        
        # Get weekly summary
        week_query = """
        SELECT DATE(scheduled_time),
               SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
               COUNT(*) as total
        FROM dose_tracking
        WHERE user_id = %s AND scheduled_time >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(scheduled_time)
        ORDER BY DATE(scheduled_time)
        """
        
        cursor.execute(week_query, (user_id,))
        week_results = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        weekly_data = []
        for week_result in week_results:
            date, taken, missed, total = week_result
            weekly_adherence = (taken / total * 100) if total > 0 else 0
            weekly_data.append({
                "date": date.isoformat(),
                "doses_taken": taken or 0,
                "doses_missed": missed or 0,
                "total_doses": total or 0,
                "adherence_percentage": round(weekly_adherence, 1)
            })
        
        return success_response({
            "user_id": user_id,
            "today": {
                "doses_taken": doses_taken,
                "doses_missed": doses_missed,
                "total_doses": total_doses,
                "adherence_percentage": round(adherence_percentage, 1)
            },
            "weekly_summary": weekly_data,
            "encouragement": get_encouragement_message(adherence_percentage)
        })
    
    except Exception as e:
        return error_response(str(e), "Error retrieving adherence summary")

def get_encouragement_message(adherence_percentage):
    """Generate encouragement based on adherence"""
    if adherence_percentage >= 90:
        return "🌟 Excellent adherence! Keep up the great work!"
    elif adherence_percentage >= 75:
        return "👍 Good job! You're doing well with your medication."
    elif adherence_percentage >= 50:
        return "💪 You're making progress. Let's keep improving!"
    else:
        return "⚠️ We noticed some missed doses. Let's work together to improve your adherence."

# ===== STEP 11: SAFETY DISCLAIMER =====

@app.route('/api/disclaimer', methods=['GET'])
def get_disclaimer():
    """Get safety disclaimer"""
    return success_response({
        "disclaimer": """
🚨 IMPORTANT SAFETY DISCLAIMER 🚨

This Medication Adherence Support System is designed to provide INFORMATIONAL SUPPORT ONLY.

⚠️ It does NOT replace professional medical advice, diagnosis, or treatment.

Always consult with your healthcare provider:
- Before starting any new medication
- If you experience any side effects
- If you have questions about your prescription
- Before changing your medication schedule
- If you have drug allergies or contraindications

In case of medical emergency, please call 911 or visit your nearest emergency room.

Your doctor, pharmacist, and healthcare team are your best resources for medication guidance.

By using this system, you acknowledge that you understand this disclaimer.
"""
    })

# ===== EXPORT & REPORTING =====

@app.route('/api/reports/adherence/<int:user_id>', methods=['GET'])
def export_adherence_report(user_id):
    """Export adherence report for healthcare provider"""
    try:
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get user info
        cursor = conn.cursor()
        cursor.execute("SELECT username, full_name, email FROM users WHERE id = %s", (user_id,))
        user_result = cursor.fetchone()
        
        if not user_result:
            cursor.close()
            close_db_connection(conn)
            return error_response("User not found", "Not Found", 404)
        
        # Get all prescriptions
        cursor.execute(
            "SELECT id, medicine_name, dosage, dosage_unit, frequency, is_confirmed FROM prescriptions WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        prescriptions = cursor.fetchall()
        
        # Get adherence summary for past 30 days
        cursor.execute("""
            SELECT DATE(scheduled_time), 
                   SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END),
                   COUNT(*)
            FROM dose_tracking
            WHERE user_id = %s AND scheduled_time >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(scheduled_time)
            ORDER BY DATE(scheduled_time)
        """, (user_id,))
        daily_reports = cursor.fetchall()
        cursor.close()
        close_db_connection(conn)
        
        # Build report
        report = {
            "report_date": datetime.now().isoformat(),
            "patient_info": {
                "username": user_result[0],
                "full_name": user_result[1],
                "email": user_result[2]
            },
            "prescriptions": [
                {
                    "id": p[0],
                    "medicine": p[1],
                    "dosage": f"{p[2]} {p[3]}",
                    "frequency": p[4],
                    "confirmed": p[5]
                } for p in prescriptions
            ],
            "adherence_data_30_days": [
                {
                    "date": str(d[0]),
                    "doses_taken": d[1] or 0,
                    "doses_missed": d[2] or 0,
                    "total_doses": d[3] or 0,
                    "adherence_percentage": round((d[1] or 0) / (d[3] or 1) * 100, 1)
                } for d in daily_reports
            ],
            "disclaimer": "This report is for informational purposes and should be reviewed with a healthcare provider."
        }
        
        return success_response(report, "Adherence report generated")
    
    except Exception as e:
        return error_response(str(e), "Error generating report")

# ===== REPORT EXPORT =====

@app.route('/api/reports/export', methods=['POST'])
def export_report():
    """Export adherence report and send via email"""
    try:
        data = request.json
        user_id = data.get("user_id")
        email = data.get("email", "")
        username = data.get("username", "")
        
        if not email or '@' not in email:
            return error_response("Valid email address required", "Validation Error", 400)
        
        conn = get_db_connection()
        if not conn:
            return error_response("Database connection failed")
        
        # Get full adherence data
        cursor = conn.cursor()
        
        # Get today's summary
        cursor.execute("""
            SELECT SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
                   SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                   COUNT(*) as total
            FROM dose_tracking 
            WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
        """, (user_id,))
        today_result = cursor.fetchone()
        
        today_taken = today_result[0] or 0
        today_missed = today_result[1] or 0
        today_total = today_result[2] or 0
        today_adherence = (today_taken / today_total * 100) if today_total > 0 else 0
        
        # Get prescriptions
        cursor.execute("""
            SELECT medicine_name, dosage, dosage_unit, frequency, start_date, end_date
            FROM prescriptions 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        prescriptions = cursor.fetchall()
        
        # Get weekly summary
        cursor.execute("""
            SELECT DATE(scheduled_time),
                   SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
                   SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                   COUNT(*) as total
            FROM dose_tracking
            WHERE user_id = %s AND scheduled_time >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(scheduled_time)
            ORDER BY DATE(scheduled_time)
        """, (user_id,))
        weekly_results = cursor.fetchall()
        
        cursor.close()
        close_db_connection(conn)
        
        # Build email content
        email_subject = f"Your Medication Adherence Report - {datetime.now().strftime('%B %d, %Y')}"
        
        email_body = f"""
Dear {username},

Your Medication Adherence Report has been generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}.

═══════════════════════════════════════════════════════════════

TODAY'S ADHERENCE SUMMARY
─────────────────────────────────────────────────────────────
Doses Taken:      {today_taken}/{today_total}
Doses Missed:     {today_missed}
Adherence Rate:   {today_adherence:.1f}%

CURRENT MEDICATIONS
─────────────────────────────────────────────────────────────
"""
        
        if prescriptions:
            for med in prescriptions:
                medicine_name, dosage, dosage_unit, frequency, start_date, end_date = med
                email_body += f"\n• {medicine_name}\n"
                email_body += f"  Dosage: {dosage} {dosage_unit or 'mg'}\n"
                email_body += f"  Frequency: {frequency}\n"
                if start_date:
                    email_body += f"  Start Date: {start_date}\n"
                if end_date:
                    email_body += f"  End Date: {end_date}\n"
        else:
            email_body += "\nNo medications currently tracked.\n"
        
        email_body += "\n\nWEEKLY ADHERENCE SUMMARY (Last 7 Days)\n"
        email_body += "─────────────────────────────────────────────────────────────\n"
        
        if weekly_results:
            total_weekly_taken = 0
            total_weekly_doses = 0
            for date, taken, missed, total in weekly_results:
                taken = taken or 0
                missed = missed or 0
                total = total or 0
                weekly_adherence = (taken / total * 100) if total > 0 else 0
                total_weekly_taken += taken
                total_weekly_doses += total
                email_body += f"{date}: {taken}/{total} doses ({weekly_adherence:.1f}%)\n"
            
            overall_weekly = (total_weekly_taken / total_weekly_doses * 100) if total_weekly_doses > 0 else 0
            email_body += f"\nWeekly Average: {overall_weekly:.1f}%\n"
        else:
            email_body += "No data available for this period.\n"
        
        email_body += """
═══════════════════════════════════════════════════════════════

RECOMMENDATIONS
─────────────────────────────────────────────────────────────
✓ Continue taking your medications as prescribed
✓ Set daily reminders for your medication times
✓ Keep a brief log of any missed doses and reasons
✓ Share this report with your healthcare provider

IMPORTANT NOTICE
─────────────────────────────────────────────────────────────
This report is for informational purposes only and should not 
replace professional medical advice. Please consult with your 
healthcare provider regarding any concerns about your medications.

═══════════════════════════════════════════════════════════════

Generated by: Pill Pal - Medication Adherence Support System
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

For more information, visit your dashboard at:
http://localhost:5000

─────────────────────────────────────────────────────────────
"""
        
        # Send email
        email_sent = send_email(email, email_subject, email_body)
        
        if email_sent:
            print(f"✓ Report emailed to {email} for user {username} ({user_id})")
            return success_response({
                "message": f"Report successfully sent to {email}",
                "user_id": user_id,
                "email": email,
                "generated_at": datetime.now().isoformat(),
                "email_sent": True
            }, "Report emailed successfully")
        else:
            print(f"⚠ Report generated but email could not be sent to {email}")
            return success_response({
                "message": f"Report generated but could not be emailed to {email}. Check .env SMTP settings.",
                "user_id": user_id,
                "email": email,
                "generated_at": datetime.now().isoformat(),
                "email_sent": False
            }, "Report generated (email not sent - check configuration)")
    
    except Exception as e:
        print(f"✗ Error exporting report: {str(e)}")
        return error_response(str(e), "Error exporting report")

@app.route('/', methods=['GET'])
def serve_frontend():
    """Serve the frontend HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>', methods=['GET'])
def serve_static(filename):
    """Serve static files (CSS, JS, etc.) — never intercept /api/ paths"""
    if filename.startswith('api/'):
        return jsonify({"status": "error", "message": "Endpoint not found", "error": f"No such API route: /{filename}"}), 404
    if os.path.exists(os.path.join('.', filename)):
        return send_from_directory('.', filename)
    # If file not found, serve index.html for frontend routing
    return send_from_directory('.', 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with detailed diagnostics"""
    try:
        import psycopg2
        db_url = os.getenv('DATABASE_URL', '')
        has_url = bool(db_url)
        db_host = os.getenv('DB_HOST', 'not set')
        
        conn = get_db_connection()
        if conn:
            # Test query to verify tables exist
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]
            cursor.close()
            close_db_connection(conn)
            return success_response({
                "status": "healthy",
                "database": "connected",
                "has_database_url": has_url,
                "tables_found": table_count
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Database connection failed",
                "has_database_url": has_url,
                "db_host_fallback": db_host,
                "hint": "Check DATABASE_URL env var on Render dashboard"
            }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "has_database_url": bool(os.getenv('DATABASE_URL', '')),
            "hint": "Connection error - check DATABASE_URL format"
        }), 503

# Auto-create database tables on startup (non-fatal — app starts even if DB isn't ready)
def init_database():
    """Create tables from schema.sql if they don't exist"""
    try:
        conn = get_db_connection(retry=False)
        if conn:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    cursor = conn.cursor()
                    cursor.execute(f.read())
                    conn.commit()
                    cursor.close()
                    print("✓ Database tables initialized")
            close_db_connection(conn)
        else:
            print("⚠ Database not available at startup — tables will be created on first successful connection")
    except Exception as e:
        print(f"⚠ Database init skipped (non-fatal): {e}")

try:
    init_database()
except Exception as e:
    print(f"⚠ init_database error caught (non-fatal): {e}")

# Start the app
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug, port=port, host='0.0.0.0')
