"""
Model Runner for Comparison Tests

Runs queries against multiple LLM models in parallel for comparison.
Supports: Google Gemini, Groq, GitHub Models (OpenAI-compatible), and Ollama local models.
"""

import asyncio
import time
import os
import httpx
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Result from running a query against a model."""
    model_name: str
    response_text: str
    latency_ms: float
    tokens_used: Dict[str, int]
    cost_estimate: float
    error: Optional[str] = None


class ModelRunner:
    """Run queries against multiple models for comparison."""
    
    # Models to test - organized by provider and role
    MODELS_TO_TEST = {
        # ===== GOOGLE GEMINI =====
        "gemini-2.0-flash": {
            "provider": "google",
            "model_name": "gemini-2.0-flash-exp",
            "temperature": 0.7,
            "role": "fast",
        },
        "gemini-2.5-flash": {
            "provider": "google",
            "model_name": "gemini-2.5-flash",
            "temperature": 0.7,
            "role": "rag",
        },
        "gemini-2.5-pro": {
            "provider": "google",
            "model_name": "gemini-2.5-pro",
            "temperature": 0.7,
            "role": "tutor",
        },
        
        # ===== GITHUB MODELS (OpenAI-compatible) =====
        "gpt-4o": {
            "provider": "github",
            "model_name": "openai/gpt-4o",
            "temperature": 0.7,
            "role": "overall",
        },
        "gpt-4.1-mini": {
            "provider": "github",
            "model_name": "openai/gpt-4.1-mini",
            "temperature": 0.7,
            "role": "router",
        },
        "o3-mini": {
            "provider": "github",
            "model_name": "openai/o3-mini",
            "temperature": 1.0,  # o3-mini requires temperature=1
            "role": "evaluator",
            "use_completion_tokens": True,  # Use max_completion_tokens instead of max_tokens
        },
        
        # ===== GROQ =====
        "groq-llama-70b": {
            "provider": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "temperature": 0.7,
            "role": "complex",
        },
        
        # ===== OLLAMA LOCAL =====
        "mistral-7b": {
            "provider": "ollama",
            "model_name": "mistral:7b-instruct",
            "temperature": 0.7,
            "role": "fast",
        },
        "qwen2-7b": {
            "provider": "ollama",
            "model_name": "qwen2:7b-instruct",
            "temperature": 0.7,
            "role": "multilingual",
        },
        "phi3-mini": {
            "provider": "ollama",
            "model_name": "phi3:mini",
            "temperature": 0.7,
            "role": "routing",
        },
        "llama3.2-3b": {
            "provider": "ollama",
            "model_name": "llama3.2:3b",
            "temperature": 0.7,
            "role": "fast-routing",
        },
    }
    
    # Cost estimates per 1K tokens (local = 0)
    COST_MAP = {
        # Google
        "gemini-2.0-flash-exp": {"input": 0.00015, "output": 0.0006},
        "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
        # GitHub Models (OpenAI pricing)
        "openai/gpt-4o": {"input": 0.005, "output": 0.015},
        "openai/gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
        "openai/o3-mini": {"input": 0.0011, "output": 0.0044},
        # Groq
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        # Ollama (local = free)
        "mistral:7b-instruct": {"input": 0, "output": 0},
        "qwen2:7b-instruct": {"input": 0, "output": 0},
        "phi3:mini": {"input": 0, "output": 0},
        "llama3.2:3b": {"input": 0, "output": 0},
    }
    
    # GitHub Models API settings
    GITHUB_API_ENDPOINT = "https://models.github.ai/inference"
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    
    # Ollama API settings
    OLLAMA_ENDPOINT = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    
    def __init__(self, system_prompt: Optional[str] = None, github_token: Optional[str] = None):
        self.system_prompt = system_prompt or "You are a helpful AI tutor for COMP 237: Introduction to AI."
        self.models = {}
        self._initialized = False
        self._http_client = None
        if github_token:
            self.GITHUB_TOKEN = github_token
    
    async def _get_http_client(self):
        """Get or create async HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    def _init_models(self):
        """Initialize all model clients lazily."""
        if self._initialized:
            return
        
        # Initialize LangChain-based models (Google, Groq)
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_groq import ChatGroq
            from app.config import settings
            
            for name, config in self.MODELS_TO_TEST.items():
                try:
                    if config["provider"] == "google":
                        self.models[name] = ChatGoogleGenerativeAI(
                            model=config["model_name"],
                            temperature=config["temperature"],
                            google_api_key=settings.google_api_key,
                        )
                        logger.info(f"✅ Initialized model: {name} (Google)")
                    elif config["provider"] == "groq":
                        self.models[name] = ChatGroq(
                            model=config["model_name"],
                            temperature=config["temperature"],
                            api_key=settings.groq_api_key,
                        )
                        logger.info(f"✅ Initialized model: {name} (Groq)")
                    elif config["provider"] in ["github", "ollama"]:
                        # These use direct HTTP calls, mark as available
                        self.models[name] = {"type": config["provider"], "config": config}
                        logger.info(f"✅ Registered model: {name} ({config['provider']})")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize {name}: {e}")
        except ImportError as e:
            logger.error(f"Failed to import model libraries: {e}")
        
        self._initialized = True
    
    async def _call_github_model(
        self,
        model_name: str,
        messages: List[Dict],
        temperature: float = 0.7,
        use_completion_tokens: bool = False,
    ) -> Dict:
        """Call GitHub Models API (OpenAI-compatible)."""
        client = await self._get_http_client()
        
        # Build request payload
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        # o3-mini and some other models require max_completion_tokens instead of max_tokens
        if use_completion_tokens:
            payload["max_completion_tokens"] = 2000
        else:
            payload["max_tokens"] = 2000
        
        response = await client.post(
            f"{self.GITHUB_API_ENDPOINT}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.GITHUB_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
    async def _call_ollama_model(
        self,
        model_name: str,
        messages: List[Dict],
        temperature: float = 0.7,
    ) -> Dict:
        """Call Ollama local API."""
        client = await self._get_http_client()
        
        response = await client.post(
            f"{self.OLLAMA_ENDPOINT}/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            },
        )
        response.raise_for_status()
        return response.json()
    
    async def run_query(
        self,
        model_name: str,
        query: str,
        timeout: float = 60.0
    ) -> ModelResponse:
        """Run a single query against a model."""
        self._init_models()
        
        if model_name not in self.models:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=0,
                tokens_used={},
                cost_estimate=0,
                error=f"Model {model_name} not initialized"
            )
        
        model = self.models[model_name]
        config = self.MODELS_TO_TEST[model_name]
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            start_time = time.perf_counter()
            
            if config["provider"] == "github":
                # GitHub Models API
                use_completion_tokens = config.get("use_completion_tokens", False)
                result = await asyncio.wait_for(
                    self._call_github_model(
                        config["model_name"],
                        messages,
                        config["temperature"],
                        use_completion_tokens=use_completion_tokens,
                    ),
                    timeout=timeout
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                response_text = result["choices"][0]["message"]["content"]
                tokens = {
                    "input": result.get("usage", {}).get("prompt_tokens", 0),
                    "output": result.get("usage", {}).get("completion_tokens", 0),
                }
                
            elif config["provider"] == "ollama":
                # Ollama local API
                result = await asyncio.wait_for(
                    self._call_ollama_model(
                        config["model_name"],
                        messages,
                        config["temperature"],
                    ),
                    timeout=timeout
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                response_text = result.get("message", {}).get("content", "")
                tokens = {
                    "input": result.get("prompt_eval_count", 0),
                    "output": result.get("eval_count", 0),
                }
                
            else:
                # LangChain models (Google, Groq)
                response = await asyncio.wait_for(
                    model.ainvoke(messages),
                    timeout=timeout
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # Handle response.content which can be str or list
                content = response.content
                if isinstance(content, list):
                    # For multi-part responses, join text parts
                    response_text = " ".join(
                        str(part.get("text", part)) if isinstance(part, dict) else str(part)
                        for part in content
                    )
                else:
                    response_text = str(content) if content else ""
                tokens = {}
                if hasattr(response, "usage_metadata"):
                    tokens = {
                        "input": response.usage_metadata.get("input_tokens", 0),
                        "output": response.usage_metadata.get("output_tokens", 0),
                    }
            
            # Estimate cost
            base_model = config["model_name"]
            cost_rates = self.COST_MAP.get(base_model, {"input": 0, "output": 0})
            cost = (
                tokens.get("input", 0) * cost_rates["input"] / 1000 +
                tokens.get("output", 0) * cost_rates["output"] / 1000
            )
            
            return ModelResponse(
                model_name=model_name,
                response_text=response_text,
                latency_ms=latency_ms,
                tokens_used=tokens,
                cost_estimate=cost,
            )
        
        except asyncio.TimeoutError:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=timeout * 1000,
                tokens_used={},
                cost_estimate=0,
                error="Timeout"
            )
        except httpx.HTTPStatusError as e:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=0,
                tokens_used={},
                cost_estimate=0,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            return ModelResponse(
                model_name=model_name,
                response_text="",
                latency_ms=0,
                tokens_used={},
                cost_estimate=0,
                error=str(e)
            )
    
    async def run_comparison(
        self,
        query: str,
        models: Optional[List[str]] = None
    ) -> Dict[str, ModelResponse]:
        """Run the same query against multiple models.
        
        GitHub models run sequentially with delay to avoid rate limits.
        Other models run in parallel.
        """
        self._init_models()
        
        models_to_run = models or list(self.models.keys())
        
        # Separate GitHub models from others to handle rate limits
        github_models = [
            m for m in models_to_run 
            if self.MODELS_TO_TEST.get(m, {}).get("provider") == "github"
        ]
        other_models = [
            m for m in models_to_run 
            if self.MODELS_TO_TEST.get(m, {}).get("provider") != "github"
        ]
        
        results = {}
        
        # Run non-GitHub models in parallel
        if other_models:
            tasks = [self.run_query(model_name, query) for model_name in other_models]
            responses = await asyncio.gather(*tasks)
            results.update({resp.model_name: resp for resp in responses})
        
        # Run GitHub models sequentially with delay to avoid rate limits
        for model_name in github_models:
            response = await self.run_query(model_name, query)
            results[model_name] = response
            # Add delay between GitHub API calls to avoid rate limits
            if model_name != github_models[-1]:  # Don't delay after last one
                await asyncio.sleep(3.0)  # 3 second delay to avoid 429 errors
        
        return results
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        self._init_models()
        return list(self.models.keys())
    
    def get_models_by_role(self, role: str) -> List[str]:
        """Get models suitable for a specific role."""
        return [
            name for name, config in self.MODELS_TO_TEST.items()
            if config.get("role") == role
        ]
    
    async def close(self):
        """Clean up HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
