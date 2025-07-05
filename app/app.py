import socket
from flask import Flask, jsonify
from pydantic_settings import BaseSettings
import psycopg2
import os
from contextlib import closing

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
            "user": self.user,
            "password": self.password,
            "dbname": self.dbname,
            "host": self.host
        }
    
    @property
    def read_connection(self):
        credentials = self.common_credentials.copy()
        credentials["port"] = self.read_port
        return psycopg2.connect(**credentials)
    
    @property
    def write_connection(self):
        credentials = self.common_credentials.copy()
        credentials["port"] = self.write_port
        return psycopg2.connect(**credentials)

def get_host_info():
    """Returns container's network information"""
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return {
        "container_hostname": hostname,
        "container_ip": ip_address,
        "app_port": os.getenv("APP_PORT", "8000")
    }

@app.route('/')
def index():
    """Main endpoint showing container and DB info"""
    host_info = get_host_info()
    
    try:
        with closing(DatabaseConnector().read_connection) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        pg_is_in_recovery(), 
                        inet_server_addr(), 
                        inet_server_port(),
                        current_database()
                    """)
                row = cur.fetchone()
                
                db_info = {
                    "role": "SLAVE" if row[0] else "MASTER",
                    "db_host": row[1],
                    "db_port": row[2],
                    "db_name": row[3]
                }
                
                return jsonify({
                    "container_info": host_info,
                    "database_info": db_info,
                    "message": "Success"
                })
                
    except Exception as e:
        return jsonify({
            "container_info": host_info,
            "error": str(e),
            "message": "Database connection failed"
        }), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", **get_host_info()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("APP_PORT", 8000)))