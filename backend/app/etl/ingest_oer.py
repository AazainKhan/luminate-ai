"""
OER Ingestion Script - Adds supplementary learning resources to ChromaDB

This script ingests Open Educational Resources (OER) to supplement COMP237 course materials:
1. Introduction to Data Science Using Python - Python basics, data structures, file I/O
2. MIT 18.657 Mathematics of Machine Learning - Linear algebra, probability, gradient descent
3. MIT 6.867 Machine Learning - Perceptron, regression, SVMs, kernel methods

These provide foundational math/programming context that the course assumes students know.

Usage:
    python backend/app/etl/ingest_oer.py --jsonl backend/data/raw/oer-sources/chroma_input.jsonl

Based on Adarsh's OER ingestion pattern.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import chromadb
from chromadb.config import Settings

from app.config import settings as app_settings
from app.rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def hash_id(*parts) -> str:
    """
    Create a unique hash ID from multiple parts.
    Ensures deterministic IDs for chunks.
    """
    combined = "::".join(str(p) for p in parts if p)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk (characters)
        overlap: Overlap between chunks (characters)
    
    Returns:
        List of text chunks
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


def parse_jsonl(path: str) -> List[Dict]:
    """
    Parse JSONL file containing OER content.
    
    Expected format:
    {
        "id": "unique-id",
        "text": "content...",
        "topic": "Math for ML",
        "subtopic": "Linear Algebra",
        "section_heading": "Vectors and Matrices",
        "source_title": "MIT 18.657",
        "source_url": "https://...",
        "difficulty_level": "Intermediate",
        "content_type": "Theory"
    }
    
    Returns:
        List of document dictionaries
    """
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                obj = json.loads(line)
                docs.append(obj)
            except json.JSONDecodeError as e:
                logger.warning(f"Line {line_num}: Invalid JSON, skipping: {e}")
                continue
    
    logger.info(f"Parsed {len(docs)} documents from {path}")
    return docs


def connect_chromadb():
    """Connect to ChromaDB Docker service"""
    try:
        client = chromadb.HttpClient(
            host=app_settings.chromadb_host,
            port=app_settings.chromadb_port,
            settings=Settings(anonymized_telemetry=False)
        )
        heartbeat = client.heartbeat()
        logger.info(f"✅ Connected to ChromaDB at {app_settings.chromadb_host}:{app_settings.chromadb_port}")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to connect to ChromaDB: {e}")
        raise


def get_or_create_collection(client, collection_name: str):
    """
    Get existing OER collection or create new one.
    
    IMPORTANT: Must use Gemini embeddings (768-dim) to match course collection.
    ChromaDB's default embeddings are 384-dim and incompatible.
    """
    # Delete existing collection if it exists (to recreate with correct embeddings)
    try:
        existing = client.get_collection(collection_name)
        logger.warning(f"Deleting existing collection '{collection_name}' to recreate with Gemini embeddings")
        client.delete_collection(collection_name)
    except Exception:
        pass
    
    logger.info(f"Creating new collection: {collection_name} with Gemini embeddings")
    
    # Create collection WITHOUT embedding function
    # We'll embed manually using Gemini to match course collection (768-dim)
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity
    )
    return collection


def upsert_oer(collection, docs: List[Dict]):
    """
    Insert OER documents into ChromaDB with chunking and Gemini embeddings.
    
    CRITICAL: Must use Gemini embeddings (768-dim) to match course collection.
    
    Args:
        collection: ChromaDB collection
        docs: List of OER documents
    """
    # Initialize Gemini embeddings (same as course collection)
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=app_settings.google_api_key
    )
    logger.info("✅ Initialized Gemini embeddings for OER (768-dim)")
    
    ids = []
    documents = []
    metadatas = []
    
    for doc in docs:
        text = doc.get("text", "").strip()
        if not text:
            logger.warning(f"Skipping document with no text: {doc.get('id', 'unknown')}")
            continue
        
        # Chunk the text for better retrieval
        chunks = chunk_text(text, chunk_size=800, overlap=100)
        
        for idx, chunk in enumerate(chunks):
            # Create unique ID using all relevant fields
            original_id = doc.get("id", "")
            topic = doc.get("topic", "")
            source_title = doc.get("source_title", "")
            section = doc.get("section_heading", "")
            
            chunk_id = hash_id("oer", original_id, topic, source_title, section, str(idx))
            ids.append(chunk_id)
            documents.append(chunk)
            
            # Build metadata (filter out None values)
            metadata = {
                "ns": "oer",
                "type": "oer_resource"
            }
            
            # Add non-None values
            if doc.get("title") or doc.get("section_heading"):
                metadata["title"] = doc.get("title") or doc.get("section_heading")
            if doc.get("source_url"):
                metadata["source_url"] = doc.get("source_url")
            if doc.get("source_title"):
                metadata["source_title"] = doc.get("source_title")
            if doc.get("id"):
                metadata["original_id"] = doc.get("id")
            if doc.get("topic"):
                metadata["topic"] = doc.get("topic")
            if doc.get("subtopic"):
                metadata["subtopic"] = doc.get("subtopic")
            if doc.get("section_heading"):
                metadata["section_heading"] = doc.get("section_heading")
            if doc.get("difficulty_level"):
                metadata["difficulty_level"] = doc.get("difficulty_level")
            if doc.get("content_type"):
                metadata["content_type"] = doc.get("content_type")
            
            metadatas.append(metadata)
    
    if ids:
        logger.info(f"Generating Gemini embeddings for {len(ids)} chunks...")
        # Generate embeddings with Gemini (768-dim)
        doc_embeddings = embeddings.embed_documents(documents)
        logger.info(f"✅ Generated {len(doc_embeddings)} embeddings")
        
        logger.info(f"Upserting {len(ids)} chunks with embeddings into collection...")
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=doc_embeddings  # Use Gemini embeddings (768-dim)
        )
        logger.info(f"✅ Successfully ingested {len(ids)} chunks from {len(docs)} documents")
    else:
        logger.warning("No valid documents to ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest OER resources into ChromaDB")
    parser.add_argument(
        "--jsonl",
        required=True,
        help="Path to JSONL file with OER content (e.g., backend/data/raw/oer-sources/chroma_input.jsonl)"
    )
    parser.add_argument(
        "--collection",
        default="oer_resources",
        help="Collection name (default: oer_resources)"
    )
    args = parser.parse_args()
    
    # Validate input file
    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        logger.error(f"❌ JSONL file not found: {jsonl_path}")
        sys.exit(1)
    
    # Connect to ChromaDB
    client = connect_chromadb()
    
    # Get or create collection
    collection = get_or_create_collection(client, args.collection)
    
    # Parse and ingest documents
    docs = parse_jsonl(args.jsonl)
    if not docs:
        logger.error("❌ No documents parsed from JSONL file")
        sys.exit(1)
    
    upsert_oer(collection, docs)
    
    # Show final stats
    logger.info(f"✅ Collection '{args.collection}' now has {collection.count()} total chunks")


if __name__ == "__main__":
    main()
