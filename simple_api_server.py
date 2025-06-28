#!/usr/bin/env python3
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
        print("\n🛑 Server stopped")
        server.shutdown()
