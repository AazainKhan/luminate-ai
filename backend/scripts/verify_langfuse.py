"""
Verify Langfuse integration
Tests that traces are being sent to Langfuse
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.observability import get_langfuse_client, create_trace, flush_langfuse
from app.agents.tutor_agent import run_agent


def test_langfuse_connection():
    """Test basic Langfuse connection"""
    print("=" * 60)
    print("LANGFUSE CONNECTION TEST")
    print("=" * 60)
    
    client = get_langfuse_client()
    
    if client is None:
        print("❌ Langfuse client not initialized")
        print("\nPlease ensure the following environment variables are set:")
        print("  - LANGFUSE_PUBLIC_KEY")
        print("  - LANGFUSE_SECRET_KEY")
        print("  - LANGFUSE_HOST or LANGFUSE_BASE_URL")
        return False
    
    print("✅ Langfuse client initialized")
    print(f"   Host: {client._base_url if hasattr(client, '_base_url') else 'configured'}")
    
    return True


def test_trace_creation():
    """Test creating a manual trace"""
    print("\n" + "=" * 60)
    print("TRACE CREATION TEST")
    print("=" * 60)
    
    try:
        trace = create_trace(
            name="test_trace",
            user_id="test_user",
            metadata={"test": "verification"}
        )
        
        if trace is None:
            print("⚠️  Trace creation returned None (Langfuse may not be configured)")
            return False
        
        print("✅ Trace created successfully")
        print(f"   Trace ID: {trace.id}")
        
        # Flush to ensure trace is sent
        flush_langfuse()
        print("✅ Trace flushed to Langfuse")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create trace: {e}")
        return False


def test_agent_with_langfuse():
    """Test running the agent with Langfuse tracing"""
    print("\n" + "=" * 60)
    print("AGENT EXECUTION TEST")
    print("=" * 60)
    
    try:
        query = "What is the course code for this class?"
        print(f"\nQuery: {query}")
        print("\nRunning agent...")
        
        result = run_agent(
            query=query,
            user_id="test_user",
            user_email="test@centennialcollege.ca"
        )
        
        print("\n✅ Agent executed successfully")
        print(f"\nResponse: {result.get('response', 'No response')[:200]}...")
        print(f"Intent: {result.get('intent')}")
        print(f"Model: {result.get('model_used')}")
        
        if result.get('error'):
            print(f"⚠️  Error: {result['error']}")
        
        print("\n📊 Check Langfuse UI for trace:")
        print("   http://localhost:3000")
        print("   Navigate to 'Traces' tab to see the execution graph")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to run agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("\n🔍 LANGFUSE INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Test 1: Connection
    connection_ok = test_langfuse_connection()
    
    if not connection_ok:
        print("\n❌ Langfuse connection failed. Please check configuration.")
        print("\nSetup instructions:")
        print("1. Go to http://localhost:3000")
        print("2. Create an account and project")
        print("3. Copy API keys from Settings → API Keys")
        print("4. Update backend/.env with:")
        print("   LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print("   LANGFUSE_SECRET_KEY=sk-lf-...")
        print("   LANGFUSE_HOST=http://observer:3000")
        return
    
    # Test 2: Trace creation
    trace_ok = test_trace_creation()
    
    # Test 3: Agent execution
    agent_ok = test_agent_with_langfuse()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Connection:      {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"Trace Creation:  {'✅ PASS' if trace_ok else '❌ FAIL'}")
    print(f"Agent Execution: {'✅ PASS' if agent_ok else '❌ FAIL'}")
    
    if connection_ok and trace_ok and agent_ok:
        print("\n🎉 All tests passed! Langfuse is properly integrated.")
        print("\n📊 View traces at: http://localhost:3000")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()

