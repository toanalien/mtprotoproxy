import os
import json
import time
import threading

PORT = 443

# File to store user data
USERS_FILE = "USERS.txt"

# Default users if file doesn't exist
DEFAULT_USERS = {
    'tg': {
        'secret': '00000000000000000000000000000001',
        'created_at': int(time.time())
    },
    'autouser': {
        'secret': '0e43c90aca5aef3ede5deb415553a993',
        'created_at': int(time.time())
    }
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

# Initialize users from file with only the secrets for backward compatibility
_users_data = load_users()
USERS = {username: user_data["secret"] for username, user_data in _users_data.items()}

def save_users():
    """Save users to file with metadata"""
    try:
        _users_data = {}
        for username, secret in USERS.items():
            # Preserve existing timestamp if exists, otherwise create new
            created_at = (_users_data.get(username, {}).get("created_at") 
                         if os.path.exists(USERS_FILE) and username in _users_data 
                         else int(time.time()))
            _users_data[username] = {
                "secret": secret,
                "created_at": created_at
            }
        with open(USERS_FILE, 'w') as f:
            json.dump(_users_data, f, indent=4)
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
    global USERS, _users_data
    
    if not isinstance(username, str) or not username:
        raise ValueError("Username must be a non-empty string")
    
    if not is_valid_secret(secret):
        raise ValueError("Secret must be a 32 character hex string")
        
    # Store secret in USERS for mtprotoproxy compatibility
    USERS[username] = secret
    
    # Store full metadata in _users_data
    _users_data[username] = {
        "secret": secret,
        "created_at": int(time.time())
    }
    
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
_users_file_last_modified = os.path.getmtime(USERS_FILE) if os.path.exists(USERS_FILE) else 0

def check_config_changed():
    """Check if users file has been modified"""
    global _users_file_last_modified
    try:
        if os.path.exists(USERS_FILE):
            current_mtime = os.path.getmtime(USERS_FILE)
            if current_mtime > _users_file_last_modified:
                _users_file_last_modified = current_mtime
                return True
    except Exception as e:
        print(f"Error checking config: {e}")
    return False

def reload_config():
    """Reload the configuration from file"""
    global USERS, _users_data
    
    try:
        # Load users from file
        _users_data = load_users()
        
        # Update USERS dict with just the secrets
        USERS.clear()
        USERS.update({username: user_data["secret"] 
                     for username, user_data in _users_data.items()})
        
    except Exception as e:
        print(f"Error reloading config: {e}")
