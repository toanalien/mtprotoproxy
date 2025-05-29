#!/usr/bin/env python3

import sys
import config
import random

def generate_random_secret():
    """Generate a random 32 character hex string"""
    return ''.join(random.choice('0123456789abcdef') for _ in range(32))

def print_usage():
    print("Usage:")
    print("  Add user:    ./manage_users.py add <username> [secret]")
    print("  Remove user: ./manage_users.py remove <username>")
    print("  List users:  ./manage_users.py list")
    print("\nNote: If secret is not provided, a random one will be generated")

def get_proxy_url(username, secret):
    """Generate proxy URL for a user"""
    import socket
    
    # Try to get the server's public IP
    try:
        # First try to get IPv4 address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            server_ip = s.getsockname()[0]
    except:
        try:
            # If IPv4 fails, try to get hostname
            server_ip = socket.gethostbyname(socket.gethostname())
        except:
            # If all fails, use localhost
            server_ip = "127.0.0.1"
    
    # Get port from config
    import config
    port = getattr(config, "PORT", 443)
    
    # Check if TLS mode is enabled
    modes = getattr(config, "MODES", {"tls": True})
    tls_domain = getattr(config, "TLS_DOMAIN", "www.google.com")
    
    # Generate proxy URL
    if modes.get("tls", False):
        # For TLS mode, prefix secret with "ee" and append domain hex
        tls_secret = "ee" + secret + tls_domain.encode().hex()
        proxy_url = f"tg://proxy?server={server_ip}&port={port}&secret={tls_secret}"
    else:
        # Regular mode
        proxy_url = f"tg://proxy?server={server_ip}&port={port}&secret={secret}"
    
    return proxy_url

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    try:
        if command == "add":
            if len(sys.argv) < 3:
                print_usage()
                return
                
            username = sys.argv[2]
            if len(sys.argv) == 4:
                secret = sys.argv[3]
            else:
                secret = generate_random_secret()
                
            config.add_user(username, secret)
            user_data = config.USERS[username]
            secret = user_data["secret"] if isinstance(user_data, dict) else user_data
            proxy_url = get_proxy_url(username, secret)
            print(f"User {username} added successfully with secret: {secret}")
            if isinstance(user_data, dict):
                print(f"Created at: {user_data['created_at']}")
            print(f"Proxy URL: {proxy_url}")
            
        elif command == "remove" and len(sys.argv) == 3:
            username = sys.argv[2]
            config.remove_user(username)
            print(f"User {username} removed successfully")
            
        elif command == "list":
            print("Current users:")
            for username, data in config.USERS.items():
                secret = data["secret"] if isinstance(data, dict) else data
                proxy_url = get_proxy_url(username, secret)
                print(f"{username}:")
                if isinstance(data, dict):
                    print(f"  Secret: {secret}")
                    print(f"  Created at: {data['created_at']}")
                    print(f"  Proxy URL: {proxy_url}")
                else:
                    print(f"  Secret: {secret}")
                    print(f"  Proxy URL: {proxy_url}")
            
        else:
            print_usage()
            
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
