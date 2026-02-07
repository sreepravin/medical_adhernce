#!/bin/bash
# Medication Adherence Support System Setup & Startup Script

echo "🏥 Medication Adherence Support System - Setup"
echo "=============================================="
echo ""

# Check Python installation
echo "✓ Checking Python installation..."
python --version

# Create/update database schema
echo ""
echo "✓ Setting up database schema..."
python << 'EOF'
from db_connection import get_db_connection, close_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute each statement
    for statement in schema.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"⚠️  {e}")
    
    conn.commit()
    cursor.close()
    close_db_connection(conn)
    print("✓ Database schema setup complete")
else:
    print("❌ Could not connect to database")
EOF

echo ""
echo "✓ Starting Flask API server..."
echo "🌐 API will be available at: http://localhost:5000"
echo "📚 API Documentation: See USAGE_GUIDE.md"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
