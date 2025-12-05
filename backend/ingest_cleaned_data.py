"""
ingest_cleaned_data.py - Ingest assessed and cleaned COMP237 course materials into ChromaDB

This script:
1. Loads the cleaned content from assess_course_data_quality.py output
2. Creates/updates ChromaDB collection with Gemini embeddings (768-dim)
3. Optionally loads concept graph into ChromaDB for GraphRAG
4. Verifies the ingestion worked

Usage:
    cd backend
    python ingest_cleaned_data.py [--reset]
    
    --reset: Delete existing collection and start fresh
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
COLLECTION_NAME = "comp237_course_materials"
COURSE_ID = "COMP237"

# Paths
CLEANED_DATA_DIR = Path(__file__).parent / "cleaned_data" / "processed"
CLEANED_CONTENT_FILE = CLEANED_DATA_DIR / "cleaned_content.json"
CONCEPT_GRAPH_FILE = CLEANED_DATA_DIR / "concept_graph.json"


def load_cleaned_content() -> List[Dict[str, Any]]:
    """Load cleaned content from assessment output."""
    if not CLEANED_CONTENT_FILE.exists():
        logger.error(f"Cleaned content file not found: {CLEANED_CONTENT_FILE}")
        logger.info("Please run: python assess_course_data_quality.py first")
        sys.exit(1)
    
    with open(CLEANED_CONTENT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} documents from {CLEANED_CONTENT_FILE}")
    return data


def load_concept_graph() -> Dict[str, Any]:
    """Load concept graph for GraphRAG."""
    if not CONCEPT_GRAPH_FILE.exists():
        logger.warning(f"Concept graph file not found: {CONCEPT_GRAPH_FILE}")
        return {"nodes": [], "edges": []}
    
    with open(CONCEPT_GRAPH_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded concept graph: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    return data


def filter_high_quality_docs(docs: List[Dict], min_score: int = 60) -> List[Dict]:
    """Filter documents by quality score and remove low-value content."""
    filtered = []
    
    for doc in docs:
        # Skip low quality documents
        if doc.get('quality_score', 0) < min_score:
            continue
        
        # Skip template/placeholder content
        content = doc.get('content', '')
        if 'Lorem ipsum' in content:
            continue
        
        # Skip very short content (less than 100 chars after stripping)
        if len(content.strip()) < 100:
            continue
        
        # Skip non-descriptive titles
        title = doc.get('title', '')
        if title.lower() in ['ultradocumentbody', 'content', 'content-blank', 'participate']:
            continue
        
        filtered.append(doc)
    
    logger.info(f"Filtered to {len(filtered)} high-quality documents (from {len(docs)})")
    return filtered


def prepare_documents_for_ingestion(docs: List[Dict]) -> tuple:
    """Prepare documents for ChromaDB ingestion."""
    ids = []
    texts = []
    metadatas = []
    
    for doc in docs:
        doc_id = doc.get('id', f"doc_{len(ids)}")
        ids.append(doc_id)
        
        # Build content text with title
        title = doc.get('title', 'Untitled')
        content = doc.get('content', '')
        
        # Include module/topic context in the text for better retrieval
        module = doc.get('module', 'Unknown')
        
        # Format: "Title\n\nModule: X\n\nContent"
        if module != 'Unknown':
            full_text = f"{title}\n\nModule: {module}\n\n{content}"
        else:
            full_text = f"{title}\n\n{content}"
        
        texts.append(full_text)
        
        # Build metadata - ChromaDB requires all values to be str, int, float, or bool (no None)
        week = doc.get('week')
        topic = doc.get('topic')
        module = doc.get('module')
        
        # Ensure module is never None (default to Unknown)
        if module is None:
            module = "Unknown"
        
        metadata = {
            "course_id": COURSE_ID,
            "resource_id": doc.get('resource_id', ''),
            "title": title,
            "module": module,
            "quality_score": doc.get('quality_score', 0),
            "content_type": doc.get('content_type', 'unknown'),
            "source": doc.get('metadata', {}).get('source', 'blackboard_export'),
            "url": doc.get('metadata', {}).get('url', ''),
            "is_chunked": doc.get('metadata', {}).get('is_chunked', False),
            "chunk_index": doc.get('metadata', {}).get('chunk_index', 0),
        }
        
        # Only add optional fields if they have values (ChromaDB doesn't accept None)
        if week is not None:
            metadata["week"] = int(week) if isinstance(week, (int, float)) else 0
        if topic:
            metadata["topic"] = str(topic)
        
        # Add detected concepts
        concepts = doc.get('concepts', [])
        if concepts:
            metadata['concepts'] = ','.join(concepts[:5])  # Limit to 5 concepts
        
        # Add links summary
        links = doc.get('links', [])
        if links:
            metadata['has_video'] = any(l.get('type') == 'mediasite_video' for l in links)
            metadata['has_external_links'] = any(l.get('type') == 'external' for l in links)
            metadata['link_count'] = len(links)
        
        metadatas.append(metadata)
    
    return ids, texts, metadatas


def create_concept_documents(graph: Dict) -> tuple:
    """Create documents from concept graph for GraphRAG."""
    ids = []
    texts = []
    metadatas = []
    
    nodes = graph.get('nodes', [])
    
    for node in nodes:
        concept_id = node.get('id', '')
        label = node.get('label', concept_id)
        doc_count = node.get('document_count', 0)
        hierarchy = node.get('hierarchy_info', {})
        
        # Build concept description
        children = hierarchy.get('children', [])
        prerequisites = hierarchy.get('prerequisites', [])
        
        description_parts = [f"Concept: {label}", f"Topic in COMP237 Introduction to AI"]
        
        if children:
            description_parts.append(f"Subtopics: {', '.join(children)}")
        if prerequisites:
            description_parts.append(f"Prerequisites: {', '.join(prerequisites)}")
        description_parts.append(f"Appears in {doc_count} course documents")
        
        text = '\n'.join(description_parts)
        
        ids.append(f"concept_{concept_id}")
        texts.append(text)
        metadatas.append({
            "course_id": COURSE_ID,
            "content_type": "concept_node",
            "concept_id": concept_id,
            "label": label,
            "document_count": doc_count,
            "has_prerequisites": len(prerequisites) > 0,
            "has_children": len(children) > 0,
        })
    
    logger.info(f"Created {len(ids)} concept documents for GraphRAG")
    return ids, texts, metadatas


def verify_ingestion(collection, embeddings, test_queries: List[str]) -> None:
    """Run verification queries against the collection."""
    logger.info("\n" + "=" * 60)
    logger.info("Verification - Testing queries:")
    logger.info("=" * 60)
    
    for query in test_queries:
        query_embedding = embeddings.embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=['documents', 'metadatas', 'distances']
        )
        
        if results['distances'] and results['distances'][0]:
            distances = results['distances'][0]
            min_dist = min(distances)
            in_scope = min_dist < 0.80
            status = "✅ IN SCOPE" if in_scope else "❌ OUT OF SCOPE"
            
            logger.info(f"\n{status} | Query: {query}")
            logger.info(f"  Closest distance: {min_dist:.3f}")
            
            if results['metadatas'] and results['metadatas'][0]:
                top_result = results['metadatas'][0][0]
                logger.info(f"  Top match: {top_result.get('title', 'N/A')} (Module: {top_result.get('module', 'N/A')})")
        else:
            logger.info(f"❓ NO RESULTS | {query}")


def main():
    parser = argparse.ArgumentParser(description='Ingest cleaned COMP237 course materials into ChromaDB')
    parser.add_argument('--reset', action='store_true', help='Delete existing collection and start fresh')
    parser.add_argument('--include-concepts', action='store_true', default=True, 
                       help='Include concept graph documents for GraphRAG')
    parser.add_argument('--min-quality', type=int, default=60,
                       help='Minimum quality score for documents (default: 60)')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("COMP237 Cleaned Content Ingestion")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Verify API key
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not set! Please set it in .env file")
        sys.exit(1)
    
    # Import ChromaDB and embeddings
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    
    # Connect to ChromaDB
    logger.info(f"Connecting to ChromaDB at {CHROMADB_HOST}:{CHROMADB_PORT}")
    client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    # Test connection
    try:
        client.heartbeat()
        logger.info("✅ ChromaDB connection successful")
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        logger.info("Make sure ChromaDB is running: docker compose up -d")
        sys.exit(1)
    
    # Handle collection
    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info(f"🗑️ Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            logger.info(f"Collection {COLLECTION_NAME} doesn't exist yet")
    
    # Initialize Gemini embeddings
    logger.info("Initializing Gemini embeddings (768-dim)...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )
    
    # Load and prepare documents
    cleaned_docs = load_cleaned_content()
    filtered_docs = filter_high_quality_docs(cleaned_docs, min_score=args.min_quality)
    
    # Prepare for ingestion
    ids, texts, metadatas = prepare_documents_for_ingestion(filtered_docs)
    
    # Add concept documents if requested
    if args.include_concepts:
        concept_graph = load_concept_graph()
        concept_ids, concept_texts, concept_metadatas = create_concept_documents(concept_graph)
        ids.extend(concept_ids)
        texts.extend(concept_texts)
        metadatas.extend(concept_metadatas)
    
    logger.info(f"\n📊 DOCUMENTS TO INGEST:")
    logger.info(f"  Content documents: {len(filtered_docs)}")
    if args.include_concepts:
        logger.info(f"  Concept documents: {len(concept_ids)}")
    logger.info(f"  Total: {len(ids)}")
    
    # Generate embeddings in batches
    logger.info("\nGenerating embeddings (this may take a while)...")
    batch_size = 50
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = embeddings.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)
        logger.info(f"  Processed {min(i+batch_size, len(texts))}/{len(texts)} documents")
    
    logger.info(f"✅ Generated {len(all_embeddings)} embeddings")
    logger.info(f"   Embedding dimension: {len(all_embeddings[0])}")
    
    # Create or get collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        logger.info(f"Using existing collection: {COLLECTION_NAME}")
        
        # If not reset, we need to upsert (delete existing + add new)
        if not args.reset:
            # Get existing IDs to check for duplicates
            existing = collection.get()
            existing_ids = set(existing.get('ids', []))
            
            # Find overlapping IDs
            new_ids = set(ids)
            overlap = existing_ids & new_ids
            
            if overlap:
                logger.info(f"Removing {len(overlap)} existing documents that will be updated...")
                collection.delete(ids=list(overlap))
    except Exception:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "l2", "course_id": COURSE_ID}
        )
        logger.info(f"Created new collection: {COLLECTION_NAME}")
    
    # Add documents in batches
    logger.info("\nAdding documents to ChromaDB...")
    
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_embeddings = all_embeddings[i:i+batch_size]
        batch_texts = texts[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas
        )
        logger.info(f"  Added {min(i+batch_size, len(ids))}/{len(ids)} documents")
    
    final_count = collection.count()
    logger.info(f"\n✅ Collection now contains {final_count} documents")
    
    # Verification
    test_queries = [
        "What is machine learning?",
        "Explain backpropagation algorithm",
        "How does gradient descent work?",
        "What are neural networks?",
        "Explain the Turing test",
        "What is natural language processing?",
        "K-nearest neighbors classification",
        "What is the capital of France?",  # Out of scope test
    ]
    
    verify_ingestion(collection, embeddings, test_queries)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📈 INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Collection: {COLLECTION_NAME}")
    logger.info(f"  Total documents: {final_count}")
    logger.info(f"  Content documents: {len(filtered_docs)}")
    if args.include_concepts:
        logger.info(f"  Concept documents: {len(concept_ids)}")
    logger.info(f"  Embedding dimension: 768 (Gemini)")
    logger.info(f"  Completed at: {datetime.now().isoformat()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
