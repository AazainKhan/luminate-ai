"""
Langfuse observability client for tracing agent executions
"""

import logging
from typing import Optional
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from app.config import settings

logger = logging.getLogger(__name__)

# Global Langfuse client
_langfuse_client: Optional[Langfuse] = None
_langfuse_handler: Optional[CallbackHandler] = None


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get or create Langfuse client instance (v3 SDK pattern)
    
    Returns:
        Langfuse client if configured, None otherwise
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    # Check if Langfuse is configured
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning("Langfuse not configured - observability disabled")
        return None
    
    try:
        # Determine host URL
        host = settings.langfuse_base_url or settings.langfuse_host
        
        # Initialize Langfuse client (v3 pattern - singleton)
        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=host,
        )
        
        # Get the singleton instance
        _langfuse_client = get_client()
        
        logger.info(f"Langfuse client initialized (host: {host})")
        return _langfuse_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse client: {e}")
        return None


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """
    Get or create Langfuse callback handler for LangChain (v3 SDK pattern)
    
    Returns:
        CallbackHandler if Langfuse is configured, None otherwise
    """
    global _langfuse_handler
    
    if _langfuse_handler is not None:
        return _langfuse_handler
    
    # Ensure Langfuse client is initialized first
    client = get_langfuse_client()
    if client is None:
        return None
    
    try:
        # In v3, CallbackHandler uses the singleton client automatically
        _langfuse_handler = CallbackHandler()
        
        logger.info("Langfuse callback handler initialized")
        return _langfuse_handler
        
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse handler: {e}")
        return None


def create_trace(name: str, user_id: Optional[str] = None, metadata: Optional[dict] = None):
    """
    Create a new Langfuse trace (v3 SDK pattern)
    
    Args:
        name: Trace name
        user_id: Optional user ID
        metadata: Optional metadata dictionary
        
    Returns:
        Span object or None if Langfuse not configured
    """
    client = get_langfuse_client()
    if client is None:
        return None
    
    try:
        # In v3, create a span (returns the span object directly, not a context manager)
        span = client.start_span(
            name=name
        )
        
        # Update trace attributes
        if user_id or metadata:
            span.update_trace(
                user_id=user_id,
                metadata=metadata or {}
            )
        
        return span
    except Exception as e:
        logger.error(f"Failed to create trace: {e}")
        return None


def flush_langfuse():
    """Flush any pending Langfuse events"""
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
        except Exception as e:
            logger.error(f"Failed to flush Langfuse: {e}")

