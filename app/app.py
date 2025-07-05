from flask import Flask
from pydantic_settings import BaseSettings
import psycopg2
import os

app = Flask(__name__)

class DatabaseSettings(BaseSettings, env_prefix="DB_"):
    host: str
    port: int
    user: str
    password: str
    dbname: str

@app.route('/')
def index():
    db_settings = DatabaseSettings()
    try:
        conn = psycopg2.connect(**db_settings.model_dump())
        cur = conn.cursor()
        cur.execute("SELECT pg_is_in_recovery(), inet_server_addr()")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return f"Status: {'SLAVE' if row[0] else 'MASTER'}, Host: {row[1]}"
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("APP_PORT", 8000))