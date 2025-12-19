import psycopg2
from datetime import datetime
from config.secrets import get_secret

def log_to_db(run_id: int, process_name: str, successful: bool, message: str):

    conn = None
    try:
        connection_string = get_secret("DB_CONN_STR")
        if not connection_string:
            print("Database connection string not found.")
            return

        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO AutomationAppLogs (RunID, LogTimestamp, ProcessName, Successful, Message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, datetime.now(), process_name, str(successful), message)
        )
        print(f"Log entry added to database for run {run_id}.")

        conn.commit()
        cur.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

