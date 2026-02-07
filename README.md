# PostgreSQL Connection Setup

## Getting Started

### 1. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Database Connection
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
2. Edit `.env` with your PostgreSQL credentials:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

### 4. Test the Connection
```bash
python main.py
```

## Project Structure
- `db_connection.py` - Database connection utilities
- `main.py` - Main application entry point
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create from .env.example)
- `.env.example` - Template for environment variables

## Common Issues

### Connection refused
- Make sure PostgreSQL is running
- Check DB_HOST and DB_PORT in .env

### Authentication failed
- Verify DB_USER and DB_PASSWORD are correct
- Check PostgreSQL user permissions

### Database not found
- Ensure the database exists in PostgreSQL
- Create it with: `CREATE DATABASE your_database_name;`

## Next Steps
1. Uncomment the example query in `main.py`
2. Replace `your_table` with your actual table name
3. Add your business logic to the main function
