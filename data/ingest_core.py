"""
ingest_core.py — Shared utilities for ingesting data into ChromaDB
"""
from __future__ import annotations
import hashlib
import re
import os
from typing import List
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config.chroma_config import CHROMA_SETTINGS
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def connect_chroma(persist_directory: str):
    """
    Connect to ChromaDB with persistence.
    Returns: (client, embedding_function)
    """
    # Use centralized settings but override the persist directory
    settings = CHROMA_SETTINGS.copy()
    settings.persist_directory = persist_directory
    
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=settings
    )
    
    # Use sentence-transformers (free, local, no API needed)
    # This is the default embedding that works offline
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    return client, embedding_function


def get_or_create_collection(client, collection_name: str, embedding_function):
    """
    Get existing collection or create a new one.
    """
    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        print(f"Using existing collection: {collection_name}")
    except Exception:
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Created new collection: {collection_name}")
    
    return collection


def clean_html(html_text: str) -> str:
    """
    Remove HTML tags and clean up text content.
    """
    if not html_text:
        return ""
    
    # Parse HTML (using html.parser which is built-in)
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            sentence_end = max(
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end),
                text.rfind('\n', start, end)
            )
            
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end < len(text) else end
    
    return chunks


def hash_id(*parts) -> str:
    """
    Create a unique hash ID from multiple parts.
    Useful for creating deterministic IDs for chunks.
    """
    combined = "::".join(str(p) for p in parts if p)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]
