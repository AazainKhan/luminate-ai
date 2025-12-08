#!/usr/bin/env python3
"""
Re-ingest course materials from processed JSON files into ChromaDB
Use this script to restore collections after data loss
"""

import json
import logging
import chromadb
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pathlib import Path
import sys

from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def reingest_course_materials():
    """Re-ingest course materials from cleaned_content.json"""
    
    # Connect to ChromaDB
    logger.info("🔗 Connecting to ChromaDB...")
    client = chromadb.HttpClient(
        host=settings.chromadb_host,
        port=settings.chromadb_port,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Initialize embeddings
    logger.info("🔗 Initializing Gemini embeddings...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.google_api_key
    )
    
    # Load cleaned content
    json_path = Path("/app/data/processed/cleaned_content.json")
    if not json_path.exists():
        logger.error(f"❌ File not found: {json_path}")
        return False
    
    logger.info(f"📂 Loading content from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        content_items = data
    else:
        content_items = data.get("content_items", [])
    
    logger.info(f"✅ Loaded {len(content_items)} content items")
    
    # Create collection
    collection_name = "comp237_course_materials"
    try:
        client.delete_collection(collection_name)
        logger.info(f"🗑️  Deleted existing collection: {collection_name}")
    except:
        pass
    
    logger.info(f"📦 Creating collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Process and ingest content
    batch_size = 20  # Process in batches to avoid memory issues
    total_chunks = 0
    
    for i in range(0, len(content_items), batch_size):
        batch = content_items[i:i + batch_size]
        documents = []
        metadatas = []
        ids = []
        
        for item in batch:
            # Extract metadata (handle both 'content' and 'text_content' fields)
            title = item.get("title", "Unknown")
            resource_id = item.get("resource_id", "unknown")
            module = item.get("module", "")
            week = item.get("week", "")
            content_type = item.get("content_type", "course_material")
            text_content = item.get("content", item.get("text_content", ""))
            
            if not text_content or len(text_content.strip()) < 50:
                continue
            
            # Create document text
            doc_text = f"Title: {title}\n\n{text_content}"
            
            # Create metadata (ensure all values are ChromaDB-compatible types)
            metadata = {
                "title": str(title) if title else "",
                "resource_id": str(resource_id) if resource_id else "",
                "module": str(module) if module else "",
                "week": str(week) if week else "",
                "content_type": str(content_type) if content_type else "course_material",
                "course_id": "COMP237"
            }
            
            documents.append(doc_text)
            metadatas.append(metadata)
            # Use a unique ID combining resource_id and index to avoid duplicates
            ids.append(f"comp237_{resource_id}_{len(ids)}")
        
        if not documents:
            continue
        
        # Generate embeddings
        logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(content_items) + batch_size - 1)//batch_size} ({len(documents)} docs)...")
        embeddings = embeddings_model.embed_documents(documents)
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        total_chunks += len(documents)
    
    logger.info(f"✅ Successfully ingested {total_chunks} documents into {collection_name}")
    return True


def reingest_embedded_resources():
    """Re-ingest embedded resources from embedded_content.json"""
    
    # Connect to ChromaDB
    logger.info("🔗 Connecting to ChromaDB...")
    client = chromadb.HttpClient(
        host=settings.chromadb_host,
        port=settings.chromadb_port,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Initialize embeddings
    logger.info("🔗 Initializing Gemini embeddings...")
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.google_api_key
    )
    
    # Load embedded content
    json_path = Path("/app/data/processed/embedded_content.json")
    if not json_path.exists():
        logger.error(f"❌ File not found: {json_path}")
        return False
    
    logger.info(f"📂 Loading content from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("embedded_items", [])
    logger.info(f"✅ Loaded {len(items)} embedded items")
    
    # Create collection
    collection_name = "embedded_resources"
    try:
        client.delete_collection(collection_name)
        logger.info(f"🗑️  Deleted existing collection: {collection_name}")
    except:
        pass
    
    logger.info(f"📦 Creating collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Process embedded items
    documents = []
    metadatas = []
    ids = []
    
    for item in items:
        source_file = item.get("source_file", "unknown")
        resource_id = item.get("associated_resource_id", "unknown")
        course_location = item.get("course_location", {})
        parent = course_location.get("parent", "Unknown Module")
        title = course_location.get("title", "Unknown Resource")
        
        for link in item.get("extracted_links", []):
            link_type = link.get("type", "unknown")
            url = link.get("url", "")
            context_text = link.get("context_text", "")
            
            # Construct document text
            doc_text = (
                f"Embedded Resource: {title}\n"
                f"Location: {parent}\n"
                f"Type: {link_type}\n"
                f"URL: {url}\n"
                f"Context: {context_text}"
            )
            
            # Construct metadata
            metadata = {
                "course_id": "COMP237",
                "content_type": "embedded_resource",
                "source_file": source_file,
                "resource_id": resource_id,
                "link_type": link_type,
                "url": url,
                "parent_module": parent,
                "title": title
            }
            
            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(f"embedded_{resource_id}_{link_type}_{len(ids)}")
    
    if documents:
        logger.info(f"🔄 Generating embeddings for {len(documents)} embedded resources...")
        embeddings = embeddings_model.embed_documents(documents)
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        logger.info(f"✅ Successfully ingested {len(documents)} embedded resources")
    
    return True


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🔄 Re-ingesting course materials into ChromaDB")
    logger.info("=" * 60)
    
    # Ingest course materials
    logger.info("\n📚 Step 1: Ingesting course materials...")
    if not reingest_course_materials():
        logger.error("❌ Failed to ingest course materials")
        sys.exit(1)
    
    # Ingest embedded resources
    logger.info("\n🎥 Step 2: Ingesting embedded resources...")
    if not reingest_embedded_resources():
        logger.error("❌ Failed to ingest embedded resources")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Re-ingestion complete!")
    logger.info("=" * 60)
