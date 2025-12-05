#!/usr/bin/env python3
"""
Verify RAG functionality by asking a course-specific question
"""
import jwt
import requests
import time
import json
import sys

# Use the secret from test_auth.py or retrieve from env if possible
JWT_SECRET = "0Dv4iB7/YR/lxnFzE2D2jM6qrTeuNDimtCMChpyrD69u6FpnVdep3EYqFnvx1HJhZPRth7qQnVKWjxIhvoGVNA=="
BACKEND_URL = "http://localhost:8000"

def create_test_token(email: str = "test@my.centennialcollege.ca", role: str = "authenticated"):
    """Create a test JWT token"""
    now = int(time.time())
    payload = {
        "aud": "authenticated",
        "exp": now + 3600,
        "iat": now - 10,
        "sub": "test-user-id-123",
        "email": email,
        "role": role,
        "app_metadata": {"provider": "email"},
        "user_metadata": {},
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_rag():
    token = create_test_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Ask a specific question about the course
    question = "What is the course code and title?"
    
    print(f"🤖 Asking Agent: '{question}'")
    
    data = {
        "messages": [{"role": "user", "content": question}],
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/stream",
            headers=headers,
            json=data,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False
            
        print("\n📥 Receiving Stream:")
        full_response = ""
        
        for line in response.iter_lines():
            if not line: continue
            decoded_line = line.decode('utf-8')
            
            if decoded_line.startswith("data:"):
                json_str = decoded_line[5:].strip()
                try:
                    data = json.loads(json_str)
                    if data["type"] == "text-delta":
                        chunk = data["textDelta"]
                        print(chunk, end="", flush=True)
                        full_response += chunk
                    elif data["type"] == "sources":
                        print("\n\n📚 Sources Found:", data["sources"])
                except:
                    pass
                    
        print("\n\n✅ Stream Complete")
        
        # Basic validation
        if "COMP 237" in full_response or "Introduction to AI" in full_response or "Artificial Intelligence" in full_response:
            print("✅ Success: Agent identified the course correctly.")
            return True
        else:
            print("⚠️ Warning: Agent response didn't explicitly name the course. Check content.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_rag()
    sys.exit(0 if success else 1)










