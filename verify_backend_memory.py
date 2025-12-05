import asyncio
import aiohttp
import json
import logging
import sys
import jwt
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
JWT_SECRET = "0Dv4iB7/YR/lxnFzE2D2jM6qrTeuNDimtCMChpyrD69u6FpnVdep3EYqFnvx1HJhZPRth7qQnVKWjxIhvoGVNA=="

def generate_token():
    """Generate a valid Supabase JWT for testing."""
    payload = {
        "sub": "557c3ac3-e6a9-4b2b-95eb-b7f57961024b",
        "email": "dev-test-user@my.centennialcollege.ca",
        "aud": "authenticated",
        "role": "authenticated",
        "exp": int(time.time()) + 3600  # 1 hour expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def test_chat_stream(session, chat_id, message, expected_context=None):
    """Send a message and stream the response."""
    url = f"{BASE_URL}/api/chat/stream"
    token = generate_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": message}],
        "stream": True,
        "chat_id": chat_id,
        "model": "gemini-2.0-flash"
    }
    
    logger.info(f"User: {message}")
    
    full_response = ""
    sources = []
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Error: {response.status} - {await response.text()}")
                return None

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if data["type"] == "text-delta":
                            full_response += data["textDelta"]
                            print(data["textDelta"], end="", flush=True)
                        elif data["type"] == "sources":
                            sources = data["sources"]
                    except json.JSONDecodeError:
                        pass
            
            print("\n") # Newline after stream
            
            if expected_context:
                if expected_context.lower() in full_response.lower():
                    logger.info(f"✅ Context verified: Found '{expected_context}' in response.")
                else:
                    logger.warning(f"⚠️ Context check failed: Did not find '{expected_context}' in response.")
            
            if sources:
                logger.info(f"Sources found: {len(sources)}")
                for s in sources:
                    logger.info(f" - {s.get('title')} ({s.get('url')})")
            
            return full_response

    except Exception as e:
        logger.error(f"Exception during request: {e}")
        return None

async def verify_memory():
    """Verify multi-turn memory."""
    chat_id = "test-memory-" + str(int(asyncio.get_event_loop().time()))
    
    async with aiohttp.ClientSession() as session:
        # Turn 1: Set context
        logger.info("--- Turn 1: Setting Context ---")
        await test_chat_stream(session, chat_id, "My name is Alice and I am studying Computer Science.")
        
        # Turn 2: Verify context
        logger.info("--- Turn 2: Verifying Memory ---")
        await test_chat_stream(session, chat_id, "What is my name and what do I study?", expected_context="Alice")
        
        # Turn 3: Complex query (trigger tools)
        logger.info("--- Turn 3: Tool Usage (Syllabus) ---")
        await test_chat_stream(session, chat_id, "What are the topics covered in COMP 237?", expected_context="AI")
        
        # Turn 4: Follow-up on tool output
        logger.info("--- Turn 4: Follow-up on Tool Output ---")
        await test_chat_stream(session, chat_id, "Tell me more about the first topic you mentioned.", expected_context="search")

if __name__ == "__main__":
    try:
        asyncio.run(verify_memory())
    except KeyboardInterrupt:
        pass
