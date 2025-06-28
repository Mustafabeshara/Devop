"""
Database helper functions for initialization and management
"""
import logging
from typing import Dict, Any
from flask import current_app

logger = logging.getLogger(__name__)

def init_database(app):
    """
    Initialize database with tables and default data
    
    Args:
        app: Flask application instance
    """
    from ..models.user import db, User, Role
    from ..models.session import BrowserSession
    from ..models.audit import AuditLog
    from ..auth.security import security_manager
    
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create default roles
            create_default_roles()
            
            # Create admin user if it doesn't exist
            create_admin_user()
            
            logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def create_default_roles():
    """Create default user roles"""
    from ..models.user import db, Role
    
    try:
        default_roles = [
            {
                'name': 'admin',
                'description': 'Administrator with full system access',
                'permissions': '["system_admin", "user_management", "container_management", "audit_access"]'
            },
            {
                'name': 'user',
                'description': 'Regular user with browser session access',
                'permissions': '["session_create", "session_manage", "code_analysis"]'
            },
            {
                'name': 'readonly',
                'description': 'Read-only access for monitoring',
                'permissions': '["session_view", "analysis_view"]'
            }
        ]
        
        created_roles = []
        for role_data in default_roles:
            # Check if role already exists
            existing_role = Role.query.filter_by(name=role_data['name']).first()
            
            if not existing_role:
                role = Role(**role_data)
                db.session.add(role)
                created_roles.append(role_data['name'])
                logger.info(f"Created role: {role_data['name']}")
            else:
                logger.info(f"Role already exists: {role_data['name']}")
        
        if created_roles:
            db.session.commit()
            logger.info(f"Created {len(created_roles)} default roles")
        
        return created_roles
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create default roles: {e}")
        raise

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    from ..models.user import db, User, Role
    from ..auth.security import security_manager
    
    try:
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@secure-kimi.local')
        admin_password = current_app.config.get('ADMIN_PASSWORD', 'SecureKimi2024!')
        
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if not existing_admin:
            # Get admin role
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                logger.error("Admin role not found. Cannot create admin user.")
                return
            
            # Create admin user
            admin_user = User(
                email=admin_email,
                username='admin',
                password=security_manager.hash_password(admin_password),
                first_name='System',
                last_name='Administrator',
                active=True,
                confirmed_at=None  # Will be set by SQLAlchemy default
            )
            
            # Assign admin role
            admin_user.roles.append(admin_role)
            
            # Set admin-specific settings
            admin_user.max_containers = 10
            admin_user.container_timeout = 7200  # 2 hours
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info(f"Created admin user: {admin_email}")
            
            # Log admin user creation
            from ..models.audit import AuditLog, EventType
            AuditLog.log_event(
                EventType.USER_CREATED,
                user=admin_user,
                message="System admin user created during initialization"
            )
            
        else:
            logger.info(f"Admin user already exists: {admin_email}")
            
            # Ensure admin has admin role
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role and admin_role not in existing_admin.roles:
                existing_admin.roles.append(admin_role)
                db.session.commit()
                logger.info("Added admin role to existing admin user")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create admin user: {e}")
        raise

def upgrade_database_schema():
    """Upgrade database schema (simple migration system)"""
    from ..models.user import db
    
    try:
        # This is a simple migration system
        # In production, use Flask-Migrate or similar
        
        # Check for schema version table
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'schema_version' not in tables:
            # Create schema version tracking
            db.engine.execute("""
                CREATE TABLE schema_version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert initial version
            db.engine.execute("INSERT INTO schema_version (version) VALUES (1)")
            logger.info("Created schema version tracking")
        
        # Get current schema version
        result = db.engine.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current_version = result[0] if result[0] else 0
        
        # Define migrations
        migrations = {
            2: migrate_to_version_2,
            3: migrate_to_version_3,
            # Add more migrations as needed
        }
        
        # Apply pending migrations
        for version, migration_func in migrations.items():
            if version > current_version:
                logger.info(f"Applying migration to version {version}")
                migration_func()
                db.engine.execute(f"INSERT INTO schema_version (version) VALUES ({version})")
                logger.info(f"Migration to version {version} completed")
        
    except Exception as e:
        logger.error(f"Database schema upgrade failed: {e}")
        raise

def migrate_to_version_2():
    """Example migration to version 2"""
    from ..models.user import db
    
    # Example: Add new column to user table
    try:
        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'avatar_url' not in columns:
            db.engine.execute("ALTER TABLE user ADD COLUMN avatar_url VARCHAR(255)")
            logger.info("Added avatar_url column to user table")
    
    except Exception as e:
        logger.error(f"Migration to version 2 failed: {e}")
        raise

def migrate_to_version_3():
    """Example migration to version 3"""
    from ..models.user import db
    
    # Example: Add indexes for performance
    try:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_user_username ON user(username)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_session_user_id ON browser_session(user_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_session_status ON browser_session(status)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id)")
        
        logger.info("Added database indexes for performance")
        
    except Exception as e:
        logger.error(f"Migration to version 3 failed: {e}")
        raise

def cleanup_database():
    """Clean up old database records"""
    from ..models.user import db
    from ..models.session import BrowserSession, SessionStatus
    from ..models.audit import AuditLog
    from datetime import datetime, timedelta
    
    try:
        cleanup_results = {}
        
        # Clean up old stopped sessions (older than 7 days)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_sessions = BrowserSession.query.filter(
            BrowserSession.stopped_at < cutoff_date,
            BrowserSession.status.in_([SessionStatus.STOPPED, SessionStatus.EXPIRED, SessionStatus.ERROR])
        ).all()
        
        for session in old_sessions:
            db.session.delete(session)
        
        cleanup_results['old_sessions'] = len(old_sessions)
        
        # Clean up old audit logs (older than 90 days, keep security events)
        audit_cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_audit_logs = AuditLog.query.filter(
            AuditLog.timestamp < audit_cutoff_date,
            AuditLog.event_type.notin_(['login_failed', 'security_violation', 'unauthorized_access'])
        ).all()
        
        for log in old_audit_logs:
            db.session.delete(log)
        
        cleanup_results['old_audit_logs'] = len(old_audit_logs)
        
        # Commit all deletions
        db.session.commit()
        
        logger.info(f"Database cleanup completed: {cleanup_results}")
        return cleanup_results
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database cleanup failed: {e}")
        raise

def backup_database(backup_path: str):
    """Create a database backup"""
    import subprocess
    import os
    
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        
        if database_url.startswith('sqlite:///'):
            # SQLite backup
            db_file = database_url.replace('sqlite:///', '')
            import shutil
            shutil.copy2(db_file, backup_path)
            logger.info(f"SQLite database backed up to: {backup_path}")
            
        elif database_url.startswith('postgresql://'):
            # PostgreSQL backup
            # Extract connection details from URL
            # This would need proper URL parsing
            subprocess.run([
                'pg_dump',
                database_url,
                '-f', backup_path
            ], check=True)
            logger.info(f"PostgreSQL database backed up to: {backup_path}")
            
        else:
            logger.warning(f"Backup not implemented for database type: {database_url}")
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise

def restore_database(backup_path: str):
    """Restore database from backup"""
    import subprocess
    import os
    
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        
        if database_url.startswith('sqlite:///'):
            # SQLite restore
            db_file = database_url.replace('sqlite:///', '')
            import shutil
            shutil.copy2(backup_path, db_file)
            logger.info(f"SQLite database restored from: {backup_path}")
            
        elif database_url.startswith('postgresql://'):
            # PostgreSQL restore
            subprocess.run([
                'psql',
                database_url,
                '-f', backup_path
            ], check=True)
            logger.info(f"PostgreSQL database restored from: {backup_path}")
            
        else:
            logger.warning(f"Restore not implemented for database type: {database_url}")
        
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        raise

def check_database_health() -> Dict[str, Any]:
    """Check database health and return status"""
    from ..models.user import db, User
    from ..models.session import BrowserSession
    from ..models.audit import AuditLog
    
    health_status = {
        'healthy': True,
        'issues': [],
        'statistics': {}
    }
    
    try:
        # Test basic connectivity
        db.session.execute('SELECT 1')
        
        # Get table counts
        health_status['statistics']['users'] = User.query.count()
        health_status['statistics']['sessions'] = BrowserSession.query.count()
        health_status['statistics']['audit_logs'] = AuditLog.query.count()
        
        # Check for any issues
        
        # Check for orphaned sessions
        orphaned_sessions = BrowserSession.query.filter(
            BrowserSession.user_id.notin_(
                db.session.query(User.id).subquery()
            )
        ).count()
        
        if orphaned_sessions > 0:
            health_status['issues'].append(f'{orphaned_sessions} orphaned sessions found')
        
        # Check for users without roles
        users_without_roles = User.query.filter(
            ~User.roles.any()
        ).count()
        
        if users_without_roles > 0:
            health_status['issues'].append(f'{users_without_roles} users without roles')
        
        # Set overall health status
        health_status['healthy'] = len(health_status['issues']) == 0
        
        logger.info(f"Database health check completed: {'healthy' if health_status['healthy'] else 'issues found'}")
        
    except Exception as e:
        health_status['healthy'] = False
        health_status['issues'].append(f'Database connectivity error: {str(e)}')
        logger.error(f"Database health check failed: {e}")
    
    return health_status
