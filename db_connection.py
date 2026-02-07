import psycopg2
from psycopg2 import sql, OperationalError
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Database configuration — supports DATABASE_URL (for Render/Railway/Heroku) or individual vars
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Fix Render's postgres:// to postgresql:// (psycopg2 requires postgresql://)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Add sslmode=require for cloud databases (Render requires SSL)
if DATABASE_URL and 'sslmode' not in DATABASE_URL:
    separator = '&' if '?' in DATABASE_URL else '?'
    DATABASE_URL = DATABASE_URL + separator + 'sslmode=require'

print(f"[DB CONFIG] DATABASE_URL set: {bool(DATABASE_URL)}, length: {len(DATABASE_URL)}")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'root')
}

# Connection timeout in seconds
CONNECTION_TIMEOUT = 10
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

def get_db_connection(retry=True):
    """
    Create and return a PostgreSQL database connection with retry logic.
    Supports DATABASE_URL (cloud deploy) or individual DB_HOST/DB_PORT/etc (local).
    """
    attempt = 0
    last_error = None
    
    while attempt < RETRY_ATTEMPTS:
        try:
            if DATABASE_URL:
                connection = psycopg2.connect(DATABASE_URL, connect_timeout=CONNECTION_TIMEOUT)
                print(f"✓ Connected to PostgreSQL via DATABASE_URL")
            else:
                connection = psycopg2.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    database=DB_CONFIG['database'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    connect_timeout=CONNECTION_TIMEOUT
                )
                print(f"✓ Connected to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
            return connection
        except (psycopg2.OperationalError, psycopg2.Error) as error:
            last_error = error
            attempt += 1
            print(f"✗ Database connection attempt {attempt}/{RETRY_ATTEMPTS} failed: {str(error)}")
            
            if attempt < RETRY_ATTEMPTS and retry:
                print(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            elif not retry:
                break
    
    # If all attempts failed, provide helpful error message
    error_msg = f"Failed to connect to PostgreSQL database after {RETRY_ATTEMPTS} attempts.\n"
    error_msg += f"Connection details:\n"
    error_msg += f"  Host: {DB_CONFIG['host']}\n"
    error_msg += f"  Port: {DB_CONFIG['port']}\n"
    error_msg += f"  Database: {DB_CONFIG['database']}\n"
    error_msg += f"  User: {DB_CONFIG['user']}\n"
    error_msg += f"Last error: {str(last_error)}\n"
    error_msg += "Please ensure:\n"
    error_msg += "  1. PostgreSQL is installed and running\n"
    error_msg += "  2. Credentials in .env are correct\n"
    error_msg += "  3. Database server is accessible at the specified host:port"
    print(error_msg)
    return None

def close_db_connection(connection):
    """
    Safely close the database connection
    """
    if connection:
        try:
            connection.close()
            print("✓ Database connection closed")
        except Exception as e:
            print(f"Warning: Error closing database connection: {e}")

def execute_query(connection, query, params=None):
    """
    Execute a SELECT query and return results
    Handles connection errors gracefully
    """
    if not connection:
        print("Error: No database connection available")
        return None
    
    try:
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        return results
    except psycopg2.Error as error:
        print(f"Error executing query: {error}")
        print(f"Query: {query}")
        if params:
            print(f"Params: {params}")
        return None
    except Exception as error:
        print(f"Unexpected error executing query: {error}")
        return None

def execute_update(connection, query, params=None):
    """
    Execute INSERT, UPDATE, or DELETE query with error handling
    """
    if not connection:
        print("Error: No database connection available")
        return False
    
    try:
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        rows_affected = cursor.rowcount
        connection.commit()
        cursor.close()
        print(f"✓ Query executed successfully. Rows affected: {rows_affected}")
        return True
    except psycopg2.Error as error:
        try:
            connection.rollback()
        except:
            pass
        print(f"Error executing update: {error}")
        print(f"Query: {query}")
        if params:
            print(f"Params: {params}")
        return False
    except Exception as error:
        try:
            connection.rollback()
        except:
            pass
        print(f"Unexpected error executing update: {error}")
        return False

if __name__ == "__main__":
    # Test the connection
    conn = get_db_connection()
    if conn:
        # Example: Query a table
        # results = execute_query(conn, "SELECT * FROM your_table LIMIT 10")
        # print(results)
        close_db_connection(conn)
