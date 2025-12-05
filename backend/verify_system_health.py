import asyncio
import os
import sys
import logging
import uuid
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.rag.langchain_chroma import get_langchain_chroma_client
from app.agents.tutor_agent import run_agent
from app.observability.langfuse_client import get_langfuse_client

async def verify_database():
    """Verify Supabase connection and table existence"""
    logger.info("🔍 Verifying Database...")
    try:
        from supabase import create_client
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        tables = ["student_mastery", "interactions", "chats", "messages"]
        for table in tables:
            try:
                # Just check if we can select from the table (limit 1)
                response = supabase.table(table).select("*", count="exact").limit(1).execute()
                count = response.count
                logger.info(f"✅ Table '{table}' exists. Row count: {count}")
            except Exception as e:
                logger.error(f"❌ Table '{table}' check failed: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def verify_chromadb():
    """Verify ChromaDB connection and document count"""
    logger.info("🔍 Verifying ChromaDB...")
    try:
        client = get_langchain_chroma_client()
        # Check collection count
        # Note: LangChain wrapper doesn't expose count directly easily, 
        # but we can try a dummy search or access the underlying client if possible.
        # For now, let's try a search.
        results = client.similarity_search_with_score("test", k=1)
        logger.info(f"✅ ChromaDB connection successful. Search returned {len(results)} results.")
        return True
    except Exception as e:
        logger.error(f"❌ ChromaDB check failed: {e}")
        return False

async def verify_observability():
    """Verify Langfuse configuration"""
    logger.info("🔍 Verifying Observability...")
    try:
        client = get_langfuse_client()
        if client:
            logger.info("✅ Langfuse client initialized successfully.")
            # We can't easily check if traces are landing without making a request and checking the UI/API
            # But initialization is a good first step.
            return True
        else:
            logger.error("❌ Langfuse client failed to initialize.")
            return False
    except Exception as e:
        logger.error(f"❌ Observability check failed: {e}")
        return False

async def verify_backend_agent():
    """Run a test query through the agent"""
    logger.info("🔍 Verifying Backend Agent...")
    try:
        query = "What is gradient descent?"
        user_id = str(uuid.uuid4())
        logger.info(f"Running query: '{query}' for user: {user_id}")
        
        # Run synchronously as run_agent is sync
        result = run_agent(query=query, user_id=user_id, user_email="test@test.com")
        
        if result.get("error"):
            logger.error(f"❌ Agent returned error: {result['error']}")
            return False
        
        response = result.get("response", "")
        if len(response) > 0:
            logger.info(f"✅ Agent responded successfully ({len(response)} chars).")
            logger.info(f"Intent: {result.get('intent')}")
            return True
        else:
            logger.error("❌ Agent returned empty response.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Agent execution failed: {e}")
        return False

async def main():
    logger.info("🚀 Starting System Health Verification")
    
    db_ok = await verify_database()
    chroma_ok = await verify_chromadb()
    obs_ok = await verify_observability()
    agent_ok = await verify_backend_agent()
    
    logger.info("\n=== Verification Summary ===")
    logger.info(f"Database:      {'✅ PASS' if db_ok else '❌ FAIL'}")
    logger.info(f"ChromaDB:      {'✅ PASS' if chroma_ok else '❌ FAIL'}")
    logger.info(f"Observability: {'✅ PASS' if obs_ok else '❌ FAIL'}")
    logger.info(f"Backend Agent: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    
    if db_ok and chroma_ok and obs_ok and agent_ok:
        logger.info("\n✅ SYSTEM IS HEALTHY")
        sys.exit(0)
    else:
        logger.error("\n❌ SYSTEM HAS ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
