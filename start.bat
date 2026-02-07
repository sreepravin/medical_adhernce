@echo off
REM Medication Adherence Support System Setup & Startup Script for Windows

echo.
echo 🏥 Medication Adherence Support System - Setup
echo =============================================
echo.

REM Check Python installation
echo ✓ Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo.
echo ✓ Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Setup database schema
echo.
echo ✓ Setting up database schema...
python -c ^
    "from db_connection import get_db_connection, close_db_connection;" ^
    "conn = get_db_connection();" ^
    "if conn:" ^
    "    cursor = conn.cursor();" ^
    "    with open('schema.sql', 'r') as f:" ^
    "        schema = f.read();" ^
    "    for statement in schema.split(';'):" ^
    "        if statement.strip():" ^
    "            try:" ^
    "                cursor.execute(statement);" ^
    "            except: pass;" ^
    "    conn.commit();" ^
    "    cursor.close();" ^
    "    close_db_connection(conn);" ^
    "    print('✓ Database schema setup complete');" ^
    "else:" ^
    "    print('❌ Could not connect to database');"

echo.
echo ✓ Starting Flask API server...
echo 🌐 API will be available at: http://localhost:5000
echo 📚 API Documentation: See USAGE_GUIDE.md
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
