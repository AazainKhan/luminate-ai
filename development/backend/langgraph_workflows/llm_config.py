"""
Centralized LLM Configuration for Luminate AI
Supports multiple LLM providers with easy switching via environment variables.

Supported Providers:
- Google Gemini (gemini-2.0-flash, gemini-1.5-pro, etc.)
- OpenAI (gpt-4, gpt-3.5-turbo, etc.)
- Anthropic Claude (claude-3-opus, claude-3-sonnet, etc.)
- Ollama (llama3.2, mistral, etc.)
- Azure OpenAI

Usage:
    from llm_config import get_llm
    
    llm = get_llm(temperature=0.3)
    response = llm.invoke("Your prompt here")

Configuration:
    Set in .env file:
    LLM_PROVIDER=gemini          # gemini, openai, anthropic, ollama, azure
    MODEL_NAME=gemini-2.0-flash   # Provider-specific model name
    GOOGLE_API_KEY=your_key       # For Gemini
    OPENAI_API_KEY=your_key       # For OpenAI
    ANTHROPIC_API_KEY=your_key    # For Anthropic
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_llm(
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
):
    """
    Get LLM instance based on configuration.
    
    Args:
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        provider: Override default provider (gemini, openai, anthropic, ollama)
        model: Override default model name
        **kwargs: Additional provider-specific parameters
        
    Returns:
        LangChain LLM instance
        
    Raises:
        ValueError: If provider is unsupported or API key is missing
    """
    # Get provider and model from env or arguments
    llm_provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
    model_name = model or os.getenv("MODEL_NAME")
    
    # Provider-specific defaults if MODEL_NAME not set
    if not model_name:
        model_defaults = {
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "ollama": "llama3.2",
            "azure": "gpt-4"
        }
        model_name = model_defaults.get(llm_provider, "gemini-2.0-flash")
    
    print(f"🤖 Initializing LLM: {llm_provider} / {model_name} (temp={temperature})")
    
    # Gemini
    if llm_provider == "gemini":
        return _get_gemini_llm(model_name, temperature, max_tokens, **kwargs)
    
    # OpenAI
    elif llm_provider == "openai":
        return _get_openai_llm(model_name, temperature, max_tokens, **kwargs)
    
    # Anthropic Claude
    elif llm_provider == "anthropic":
        return _get_anthropic_llm(model_name, temperature, max_tokens, **kwargs)
    
    # Ollama (local)
    elif llm_provider == "ollama":
        return _get_ollama_llm(model_name, temperature, max_tokens, **kwargs)
    
    # Azure OpenAI
    elif llm_provider == "azure":
        return _get_azure_llm(model_name, temperature, max_tokens, **kwargs)
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {llm_provider}. "
            f"Supported: gemini, openai, anthropic, ollama, azure"
        )


def _get_gemini_llm(model: str, temperature: float, max_tokens: Optional[int], **kwargs):
    """Get Google Gemini LLM instance."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "langchain-google-genai not installed. "
            "Run: pip install langchain-google-genai"
        )
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment. "
            "Get one at: https://aistudio.google.com/apikey"
        )
    
    params = {
        "model": model,
        "temperature": temperature,
        "google_api_key": api_key,
        **kwargs
    }
    
    if max_tokens:
        params["max_output_tokens"] = max_tokens
    
    return ChatGoogleGenerativeAI(**params)


def _get_openai_llm(model: str, temperature: float, max_tokens: Optional[int], **kwargs):
    """Get OpenAI LLM instance."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Run: pip install langchain-openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Get one at: https://platform.openai.com/api-keys"
        )
    
    params = {
        "model": model,
        "temperature": temperature,
        "openai_api_key": api_key,
        **kwargs
    }
    
    if max_tokens:
        params["max_tokens"] = max_tokens
    
    return ChatOpenAI(**params)


def _get_anthropic_llm(model: str, temperature: float, max_tokens: Optional[int], **kwargs):
    """Get Anthropic Claude LLM instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic not installed. "
            "Run: pip install langchain-anthropic"
        )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Get one at: https://console.anthropic.com/settings/keys"
        )
    
    params = {
        "model": model,
        "temperature": temperature,
        "anthropic_api_key": api_key,
        **kwargs
    }
    
    if max_tokens:
        params["max_tokens"] = max_tokens
    
    return ChatAnthropic(**params)


def _get_ollama_llm(model: str, temperature: float, max_tokens: Optional[int], **kwargs):
    """Get Ollama (local) LLM instance."""
    try:
        from langchain_community.llms import Ollama
    except ImportError:
        raise ImportError(
            "langchain-community not installed. "
            "Run: pip install langchain-community"
        )
    
    params = {
        "model": model,
        "temperature": temperature,
        **kwargs
    }
    
    if max_tokens:
        params["num_predict"] = max_tokens
    
    return Ollama(**params)


def _get_azure_llm(model: str, temperature: float, max_tokens: Optional[int], **kwargs):
    """Get Azure OpenAI LLM instance."""
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Run: pip install langchain-openai"
        )
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", model)
    
    if not api_key or not endpoint:
        raise ValueError(
            "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT required. "
            "See: https://learn.microsoft.com/en-us/azure/ai-services/openai/"
        )
    
    params = {
        "azure_deployment": deployment,
        "temperature": temperature,
        "azure_endpoint": endpoint,
        "api_key": api_key,
        **kwargs
    }
    
    if max_tokens:
        params["max_tokens"] = max_tokens
    
    return AzureChatOpenAI(**params)


def get_available_providers() -> Dict[str, bool]:
    """
    Check which LLM providers are available (have API keys).
    
    Returns:
        Dictionary of provider names to availability status
    """
    return {
        "gemini": bool(os.getenv("GOOGLE_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "ollama": True,  # Always available if installed
        "azure": bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))
    }


def list_available_models() -> Dict[str, list]:
    """
    List recommended models for each provider.
    
    Returns:
        Dictionary of provider to list of model names
    """
    return {
        "gemini": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ],
        "openai": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        "ollama": [
            "llama3.2",
            "llama3.1",
            "mistral",
            "mixtral",
            "phi3",
            "gemma2"
        ],
        "azure": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo"
        ]
    }


if __name__ == "__main__":
    """Test the LLM configuration."""
    print("\n" + "="*70)
    print("LLM CONFIGURATION TEST")
    print("="*70)
    
    # Check available providers
    print("\n📋 Available Providers:")
    providers = get_available_providers()
    for provider, available in providers.items():
        status = "✓ Available" if available else "✗ Not configured"
        print(f"  {provider:12s}: {status}")
    
    # List models
    print("\n📚 Recommended Models:")
    models = list_available_models()
    for provider, model_list in models.items():
        print(f"\n  {provider.upper()}:")
        for model in model_list[:3]:  # Show top 3
            print(f"    - {model}")
    
    # Test LLM instantiation
    print("\n" + "="*70)
    print("Testing LLM Instantiation")
    print("="*70)
    
    try:
        llm = get_llm(temperature=0.3)
        print("\n✓ LLM initialized successfully")
        
        # Test inference
        print("\n🧪 Testing inference...")
        response = llm.invoke("Say 'Hello from Luminate AI!' in exactly 5 words.")
        response_text = response.content if hasattr(response, 'content') else str(response)
        print(f"Response: {response_text}")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
