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
            (str(run_id), datetime.now(), process_name, str(successful), message)
        )
        print(f"Log entry added to database for run {run_id}.")

        conn.commit()
        cur.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def bill_already_retrieved(process_name: str) -> bool:

    conn = None
    try:
        connection_string = get_secret("DB_CONN_STR")
        if not connection_string:
            print("Database connection string not found.")
            return False

        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1 FROM AutomationAppLogs
            WHERE ProcessName = %s
              AND Successful = 'True'
              AND LogTimestamp >= date_trunc('month', CURRENT_DATE)
            LIMIT 1
            """,
            (process_name,)
        )
        retrieved = cur.fetchone() is not None
        cur.close()
        return retrieved

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()
