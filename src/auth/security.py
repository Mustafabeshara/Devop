"""
Security manager for handling authentication, encryption, and security policies
"""
import bcrypt
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from flask import current_app
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bleach
import re

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self._fernet_key = None
        self._cipher_suite = None
    
    @property
    def cipher_suite(self):
        """Get or create cipher suite for encryption"""
        if self._cipher_suite is None:
            if self._fernet_key is None:
                # Generate key from app secret
                password = current_app.config['SECRET_KEY'].encode()
                salt = b'stable_salt_for_app'  # Use a stable salt for consistency
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self._fernet_key = key
            
            self._cipher_suite = Fernet(self._fernet_key)
        
        return self._cipher_suite
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except (ValueError, TypeError):
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def generate_vnc_password(self) -> str:
        """Generate a secure VNC password (8 characters for VNC compatibility)"""
        return secrets.token_urlsafe(6)[:8]
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        
        encrypted = self.cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return encrypted_data  # Return as-is if decryption fails
    
    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for 2FA"""
        return pyotp.random_base32()
    
    def generate_totp_qr_code(self, secret: str, user_email: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Cloud Browser Service"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Convert to base64 for embedding in HTML
        img_data = base64.b64encode(img_buffer.read()).decode()
        return f"data:image/png;base64,{img_data}"
    
    def verify_totp_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 1 step tolerance
        except Exception:
            return False
    
    def sanitize_input(self, input_text: str, allowed_tags: list = None) -> str:
        """Sanitize user input to prevent XSS"""
        if not input_text:
            return input_text
        
        if allowed_tags is None:
            allowed_tags = []
        
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            input_text,
            tags=allowed_tags,
            attributes={},
            strip=True
        )
        
        return cleaned.strip()
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format and security"""
        if not url:
            return False
        
        # Basic URL pattern validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False
        
        # Block dangerous schemes and internal IPs
        dangerous_schemes = ['javascript:', 'data:', 'file:', 'ftp:']
        for scheme in dangerous_schemes:
            if url.lower().startswith(scheme):
                return False
        
        # Block private IP ranges (basic check)
        private_ips = ['127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.']
        for private_ip in private_ips:
            if private_ip in url:
                return False
        
        return True
    
    def check_password_strength(self, password: str) -> dict:
        """Check password strength and return analysis"""
        if not password:
            return {
                'valid': False,
                'score': 0,
                'errors': ['Password is required']
            }
        
        errors = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        else:
            score += 1
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            errors.append('Password must contain lowercase letters')
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            errors.append('Password must contain uppercase letters')
        
        if re.search(r'\d', password):
            score += 1
        else:
            errors.append('Password must contain numbers')
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            errors.append('Password must contain special characters')
        
        # Length bonus
        if len(password) >= 12:
            score += 1
        
        # No common patterns
        common_patterns = ['123', 'abc', 'password', 'admin', 'qwerty']
        if any(pattern in password.lower() for pattern in common_patterns):
            errors.append('Password contains common patterns')
            score = max(0, score - 1)
        
        return {
            'valid': len(errors) == 0,
            'score': min(score, 5),  # Max score of 5
            'errors': errors,
            'strength': self._get_strength_label(score)
        }
    
    def _get_strength_label(self, score: int) -> str:
        """Get password strength label from score"""
        if score <= 1:
            return 'Very Weak'
        elif score <= 2:
            return 'Weak'
        elif score <= 3:
            return 'Fair'
        elif score <= 4:
            return 'Good'
        else:
            return 'Strong'
    
    def generate_secure_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    def is_safe_redirect_url(self, url: str) -> bool:
        """Check if URL is safe for redirects"""
        if not url:
            return False
        
        # Only allow relative URLs or same-origin URLs
        if url.startswith('/'):
            return True
        
        # Allow same origin
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            # Only allow http/https schemes
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check if it's the same host (implement based on your needs)
            # For now, block all external redirects
            return False
        except Exception:
            return False
    
    def log_security_event(self, event_type: str, user_id: int = None, 
                          ip_address: str = None, details: dict = None):
        """Log security events for monitoring"""
        from ..models.audit import AuditLog, EventType, SeverityLevel
        
        # Map event types
        event_mapping = {
            'login_failed': EventType.LOGIN_FAILED,
            'account_locked': EventType.ACCOUNT_LOCKED,
            'suspicious_activity': EventType.SUSPICIOUS_ACTIVITY,
            'security_violation': EventType.SECURITY_VIOLATION,
            'rate_limit_exceeded': EventType.RATE_LIMIT_EXCEEDED
        }
        
        event_enum = event_mapping.get(event_type, EventType.SECURITY_VIOLATION)
        
        AuditLog.log_event(
            event_enum,
            user_id=user_id,
            ip_address=ip_address,
            metadata=details or {},
            severity=SeverityLevel.HIGH
        )

# Global security manager instance
security_manager = SecurityManager()
