#!/usr/bin/env python3
"""
Test script to verify JWT authentication is working
"""
import jwt
import requests
import time
from datetime import datetime, timedelta

# Load the JWT secret from .env
JWT_SECRET = "0Dv4iB7/YR/lxnFzE2D2jM6qrTeuNDimtCMChpyrD69u6FpnVdep3EYqFnvx1HJhZPRth7qQnVKWjxIhvoGVNA=="
BACKEND_URL = "http://localhost:8000"

# Create a test JWT token
def create_test_token(email: str = "test@student.example.com", role: str = "authenticated"):
    """Create a test JWT token that mimics Supabase's format"""
    now = int(time.time())
    payload = {
        "aud": "authenticated",
        "exp": now + 3600,  # 1 hour from now
        "iat": now - 10,  # 10 seconds ago to account for clock skew
        "sub": "test-user-id-123",
        "email": email,
        "role": role,
        "app_metadata": {
            "provider": "email",
        },
        "user_metadata": {},
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def test_chat_endpoint():
    """Test the chat streaming endpoint"""
    # Use an institutional email that will pass role check
    token = create_test_token(email="test@my.centennialcollege.ca")
    
    print(f"Generated test token: {token[:50]}...")
    print(f"\nTesting {BACKEND_URL}/api/chat/stream")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "Hello, this is a test message"}
        ],
        "conversation_id": "test-conv-123",
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/stream",
            headers=headers,
            json=data,
            stream=True,
            timeout=30,
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n✅ Authentication successful!")
            print("\nStreaming response:")
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))
                    # Only print first few lines to avoid spam
                    break
        else:
            print(f"\n❌ Authentication failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Luminate AI Backend Authentication")
    print("=" * 60)
    test_chat_endpoint()
