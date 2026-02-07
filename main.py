from db_connection import get_db_connection, close_db_connection, execute_query

def main():
    """
    Main application entry point
    """
    connection = get_db_connection()
    
    if connection:
        # Example: Execute a query
        # results = execute_query(connection, "SELECT version();")
        # if results:
        #     print("PostgreSQL version:", results[0][0])
        
        close_db_connection(connection)
    else:
        print("Failed to connect to the database")

if __name__ == "__main__":
    main()
