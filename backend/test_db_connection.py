import os
import sys
import pymysql
from dotenv import load_dotenv

# Load backend/.env
backend_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(backend_dir, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "carewatch_db")


def check_and_initialize_db():
    """Verify MySQL connectivity and ensure carewatch_db database exists."""
    print(f"Connecting to MySQL Server at {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5,
        )
        print("Connected to MySQL Server successfully.")

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version;")
            server_version = cursor.fetchone()
            print(f"MySQL Version: {server_version['version']}")

            # Create database if it does not exist
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            print(f"Database `{DB_NAME}` verified/created successfully.")

            cursor.execute(f"USE `{DB_NAME}`;")
            cursor.execute("SELECT DATABASE() AS current_db;")
            current_db = cursor.fetchone()
            print(f"Active Database: {current_db['current_db']}")

        connection.close()
        return True, "Success"
    except pymysql.MySQLError as err:
        return False, str(err)


if __name__ == "__main__":
    success, message = check_and_initialize_db()
    if not success:
        print(f"MySQL Connection Error: {message}")
        sys.exit(1)
    print("Database verification completed.")

