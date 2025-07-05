from flask import Flask
from pydantic_settings import BaseSettings
import psycopg2
import os

app = Flask(__name__)

class DatabaseSettings(BaseSettings, env_prefix="DB_"):
    host: str
    write_port: int
    read_port: int
    user: str
    password: str
    dbname: str

class DatabaseConnector(DatabaseSettings):
    @property
    def common_credentials(self):
        return {
            "user":self.user,
            "password":self.password,
            "dbname":self.dbname,
            "host":self.host
        }
    @property
    def read_connection(self):
        read_credentials = self.common_credentials
        read_credentials.update({
            "port":self.read_port
        })
        return psycopg2.connect(**read_credentials)
    
    @property
    def write_connection(self):
        write_credentials = self.common_credentials
        write_credentials.update({
            "port":self.read_port
        })
        return psycopg2.connect(**write_credentials)

@app.route('/')
def index():
    db_connector = DatabaseConnector()
    try:
        conn = db_connector.read_connection
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