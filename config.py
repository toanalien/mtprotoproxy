import os
import json
import time
import threading

PORT = 443

# File to store user data
USERS_FILE = "USERS.txt"

# Default users if file doesn't exist
DEFAULT_USERS = {
    'tg': '00000000000000000000000000000001',
    'autouser': '0e43c90aca5aef3ede5deb415553a993',
}

MODES = {'classic': False, 'secure': False, 'tls': True}

# Prometheus exporter host and port for the dedicated endpoint
PROMETHEUS_HOST = "0.0.0.0"
PROMETHEUS_PORT = 9100

# Prometheus scrapers whitelist for safety
PROMETHEUS_SCRAPERS = []

def load_users():
    """Load users from file or create with defaults if not exists"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create file with default users if it doesn't exist
            with open(USERS_FILE, 'w') as f:
                json.dump(DEFAULT_USERS, f, indent=4)
            return DEFAULT_USERS.copy()
    except Exception as e:
        print(f"Error loading users: {e}")
        return DEFAULT_USERS.copy()

# Initialize users from file
USERS = load_users()

def save_users():
    """Save users to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(USERS, f, indent=4)
    except Exception as e:
        print(f"Error saving users: {e}")

def is_valid_secret(secret):
    """Validate if secret is a valid 32 character hex string"""
    if len(secret) != 32:
        return False
    try:
        int(secret, 16)
        return True
    except ValueError:
        return False

def add_user(username, secret):
    """Add a new user with their secret"""
    global USERS
    
    if not isinstance(username, str) or not username:
        raise ValueError("Username must be a non-empty string")
    
    if not is_valid_secret(secret):
        raise ValueError("Secret must be a 32 character hex string")
        
    USERS[username] = secret
    save_users()
    
    return True

def remove_user(username):
    """Remove a user"""
    global USERS
    
    if username not in USERS:
        raise ValueError(f"User {username} not found")
    
    del USERS[username]
    save_users()
    
    return True

# Set up file monitoring for hot reload
_last_modified = os.path.getmtime(USERS_FILE) if os.path.exists(USERS_FILE) else 0

def check_config_changed():
    """Check if users file has been modified"""
    global _last_modified
    try:
        if os.path.exists(USERS_FILE):
            current_mtime = os.path.getmtime(USERS_FILE)
            if current_mtime > _last_modified:
                return True
    except Exception as e:
        print(f"Error checking config: {e}")
    return False

def reload_config():
    """Reload the configuration from file"""
    global USERS, _last_modified
    
    try:
        # Load users from file
        new_users = load_users()
        
        # Update users
        USERS.clear()
        USERS.update(new_users)
        
        # Update last modified time
        _last_modified = os.path.getmtime(USERS_FILE) if os.path.exists(USERS_FILE) else 0
        
    except Exception as e:
        print(f"Error reloading config: {e}")
