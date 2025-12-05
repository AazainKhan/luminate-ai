"""
Langfuse observability client for tracing agent executions
"""

import logging
import time
from typing import Optional
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from app.config import settings

logger = logging.getLogger(__name__)

# Model cost definitions (per 1K tokens) - update these based on current pricing
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},  # Stable: best price-performance
    "gemini-2.5-flash-lite": {"input": 0.000038, "output": 0.00015},  # Ultra fast, cost-efficient
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},  # Advanced thinking model
    "gemini-2.0-flash": {"input": 0.000075, "output": 0.0003},  # Previous gen workhorse
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> dict:
    """
    Calculate cost details for model usage
    
    Args:
        model_name: Name of the model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Dictionary with cost breakdown
    """
    # Normalize model name for cost lookup
    normalized_name = model_name.lower()
    for key in MODEL_COSTS:
        if key in normalized_name:
            costs = MODEL_COSTS[key]
            input_cost = (input_tokens / 1000) * costs["input"]
            output_cost = (output_tokens / 1000) * costs["output"]
            return {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": input_cost + output_cost,
                "model": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
    
    # Return zero costs for unknown models
    return {
        "input_cost": 0.0,
        "output_cost": 0.0,
        "total_cost": 0.0,
        "model": model_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }

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


def create_trace(name: str, user_id: Optional[str] = None, session_id: Optional[str] = None, metadata: Optional[dict] = None,
                environment: str = "development", version: Optional[str] = None, release: Optional[str] = None,
                tags: Optional[list] = None, input_data: Optional[dict] = None):
    """
    Create a new Langfuse trace with comprehensive metadata (v3 SDK pattern)
    
    Args:
        name: Trace name
        user_id: Optional user ID
        session_id: Optional session ID
        metadata: Optional metadata dictionary (propagated to all child observations)
        environment: Environment tag (development, staging, production)
        version: Version tag for tracking deployments
        release: Release identifier
        tags: List of tags for categorization
        input_data: Input data to log at trace level
        
    Returns:
        Span object or None if Langfuse not configured
    """
    client = get_langfuse_client()
    if client is None:
        return None
    
    try:
        # Prepare propagated metadata - these will be inherited by child observations
        propagated_metadata = {
            "environment": environment,
            "system_version": version or "1.0.0",
            "request_timestamp": str(int(time.time())),
            "agent_architecture": "governor-supervisor-agent",
            "course_id": "COMP237",
            **(metadata or {})
        }
        
        # In v3, create a span with input data
        span = client.start_span(
            name=name,
            input=input_data  # Set the input data on the span
        )
        
        # Update trace attributes with compatible parameters only
        span.update_trace(
            user_id=user_id,
            session_id=session_id,
            metadata=propagated_metadata,  # These propagate to child observations
            tags=tags or ["tutor-agent", "comp237"],
            input=input_data  # Also set input at trace level
        )
        
        return span
    except Exception as e:
        logger.error(f"Failed to create trace: {e}")
        return None


def create_observation(parent_span, name: str, observation_type: str, input_data: Optional[dict] = None,
                      metadata: Optional[dict] = None, model: Optional[str] = None, 
                      model_parameters: Optional[dict] = None):
    """
    Create a typed observation with proper classification
    
    Args:
        parent_span: Parent span to attach observation to
        name: Observation name
        observation_type: One of: agent, tool, chain, retriever, evaluator, guardrail, generation, embedding, span, event
        input_data: Input data for the observation
        metadata: Non-propagated metadata specific to this observation
        model: Model name if applicable
        model_parameters: Model configuration if applicable
        
    Returns:
        Child observation span
    """
    if not parent_span:
        return None
        
    try:
        child_span = parent_span.start_as_current_span(
            name=name,
            input=input_data,
            metadata=metadata or {},
        )
        
        # Update with proper observation type and model info
        child_span.update(
            as_type=observation_type,  # This sets the observation type in Langfuse
            model=model,
            model_parameters=model_parameters or {}
        )
        
        return child_span
    except Exception as e:
        logger.error(f"Failed to create {observation_type} observation: {e}")
        return None


def create_child_span_from_state(state: dict, name: str, input_data: Optional[dict] = None,
                                 metadata: Optional[dict] = None):
    """
    Create a child span linked to the root trace using the parent span object from state.
    
    This is the CORRECT way to create nested spans in Langfuse v3:
    - Uses parent_span.start_span() instead of client.start_span(trace_context=...)
    - Ensures proper parent-child relationship in trace hierarchy
    
    Args:
        state: Agent state containing 'langfuse_root_span' key
        name: Name for the child span
        input_data: Input data for the observation
        metadata: Additional metadata
        
    Returns:
        Child span object that MUST be ended with span.end()
    """
    parent_span = state.get("langfuse_root_span")
    if not parent_span:
        # Fallback: No parent span available, log warning
        logger.debug(f"No parent span in state for child span '{name}' - span will be orphaned")
        return None
    
    try:
        # Use parent_span.start_span() for proper nesting (NOT client.start_span())
        child_span = parent_span.start_span(
            name=name,
            input=input_data,
            metadata=metadata or {}
        )
        
        return child_span
    except Exception as e:
        logger.error(f"Failed to create child span '{name}': {e}")
        return None


def update_observation_with_usage(observation, output_data: Optional[dict] = None, 
                                 usage_details: Optional[dict] = None, cost_details: Optional[dict] = None,
                                 level: str = "DEFAULT", latency_seconds: Optional[float] = None):
    """
    Update observation with output, usage, and cost tracking
    
    Args:
        observation: Langfuse observation to update
        output_data: Output data
        usage_details: Token usage details {"input": int, "output": int, "total": int, "unit": "TOKENS"}
        cost_details: Cost breakdown {"input_cost": float, "output_cost": float, "total_cost": float}
        level: Log level (DEBUG, DEFAULT, WARNING, ERROR)
        latency_seconds: Processing latency in seconds
    """
    if not observation:
        return
        
    try:
        update_params = {
            "output": output_data,
            "level": level
        }
        
        if usage_details:
            update_params["usage_details"] = usage_details
            
        if cost_details:
            update_params["cost_details"] = cost_details
            
        if latency_seconds is not None:
            update_params["latency"] = latency_seconds
            
        observation.update(**update_params)
        
    except Exception as e:
        logger.error(f"Failed to update observation with usage: {e}")


def flush_langfuse():
    """Flush any pending Langfuse events"""
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
        except Exception as e:
            logger.error(f"Failed to flush Langfuse: {e}")

