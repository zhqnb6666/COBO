import urllib

import psycopg2
from psycopg2 import OperationalError

# Database configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "taco_db"
DB_USER = "zhq"
DB_PASSWORD = "abc@1234"

encoded_password = urllib.parse.quote(DB_PASSWORD)

DATABASE_URL = f'postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


def test_connection():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        # print("Connection to the database was successful.")
        connection.close()
    except OperationalError as e:
        print(f"Error: Unable to connect to the database\n{e}")

# Run the test
# test_connection()