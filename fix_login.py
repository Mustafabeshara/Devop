#!/usr/bin/env python3
"""
Quick fix for the Kimi-Dev login issue
Creates a simple database and admin user for authentication
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def create_database():
    """Create the database and admin user"""
    db_path = "/workspace/cloud-browser-backend/database/app.db"
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            role TEXT DEFAULT 'user',
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS browser_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            browser_type TEXT,
            status TEXT,
            container_id TEXT,
            vnc_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create audit table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Hash the admin password
    password = "SecureKimi2024!"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Insert admin user
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (email, username, password_hash, first_name, last_name, role, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin@secure-kimi.local',
            'admin',
            password_hash,
            'Admin',
            'User',
            'admin',
            True
        ))
        
        conn.commit()
        print("✅ Database created successfully!")
        print("✅ Admin user created:")
        print("   Email: admin@secure-kimi.local")
        print("   Password: SecureKimi2024!")
        print("   Role: admin")
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️ User might already exist: {e}")
    
    # Verify the user was created
    cursor.execute("SELECT email, username, role FROM users WHERE email = ?", 
                  ('admin@secure-kimi.local',))
    user = cursor.fetchone()
    
    if user:
        print(f"✅ Verified admin user: {user[0]} ({user[1]}) - {user[2]}")
    else:
        print("❌ Failed to create admin user")
    
    conn.close()
    
    return db_path

def create_simple_api():
    """Create a simple API server for authentication"""
    api_code = '''#!/usr/bin/env python3
"""
Simple API server for Kimi-Dev authentication
"""

import sqlite3
import hashlib
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os

class KimiDevAPI(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/auth/login':
            self.handle_login()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith('/api/health'):
            self.handle_health()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_login(self):
        """Handle login requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                self.send_json_response({
                    'success': False,
                    'message': 'Email and password required'
                }, 400)
                return
            
            # Check credentials
            db_path = '/workspace/cloud-browser-backend/database/app.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                "SELECT id, email, username, role FROM users WHERE email = ? AND password_hash = ? AND active = 1",
                (email, password_hash)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user:
                response = {
                    'success': True,
                    'message': 'Login successful',
                    'data': {
                        'access_token': 'mock-jwt-token-' + str(user[0]),
                        'user': {
                            'id': user[0],
                            'email': user[1],
                            'username': user[2],
                            'role': user[3]
                        }
                    }
                }
                self.send_json_response(response)
            else:
                self.send_json_response({
                    'success': False,
                    'message': 'Invalid credentials'
                }, 401)
                
        except Exception as e:
            self.send_json_response({
                'success': False,
                'message': f'Login error: {str(e)}'
            }, 500)
    
    def handle_health(self):
        """Handle health check requests"""
        response = {
            'status': 'healthy',
            'timestamp': '2025-06-27T20:50:00Z',
            'version': '1.0.0',
            'message': 'Kimi-Dev API is running'
        }
        self.send_json_response(response)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 5001), KimiDevAPI)
    print("🚀 Kimi-Dev API Server starting on http://localhost:5001")
    print("✅ Health check: http://localhost:5001/api/health")
    print("🔐 Login endpoint: http://localhost:5001/api/auth/login")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped")
        server.shutdown()
'''
    
    with open('/workspace/simple_api_server.py', 'w') as f:
        f.write(api_code)
    
    os.chmod('/workspace/simple_api_server.py', 0o755)
    print("✅ Simple API server created: /workspace/simple_api_server.py")

def main():
    """Main function"""
    print("🔧 Fixing Kimi-Dev login issue...")
    print("=" * 40)
    
    # Create database and admin user
    db_path = create_database()
    print(f"📄 Database created at: {db_path}")
    
    # Create simple API server
    create_simple_api()
    
    print("\n🎉 Login fix completed!")
    print("\n📋 Next steps:")
    print("1. Start the API server: python3 /workspace/simple_api_server.py")
    print("2. Visit: https://nybbgll9qi.space.minimax.io")
    print("3. Login with: admin@secure-kimi.local / SecureKimi2024!")
    print("\n⚠️ Note: The API server needs to be running for login to work")

if __name__ == "__main__":
    main()
