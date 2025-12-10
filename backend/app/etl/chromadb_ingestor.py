"""
ChromaDB Ingestion Script

Ingests enriched sources into ChromaDB collections for RAG retrieval.
Creates multiple collections for different source types:
- comp237_course_materials: Main course content with Blackboard links
- comp237_media: Mediasite and YouTube videos  
- comp237_images: Analyzed course images
- comp237_oer: OER supplementary materials

Uses Gemini embeddings (768-dim) for consistency with RAG retrieval.

Usage:
    python -m app.etl.chromadb_ingestor

Output:
    Populates ChromaDB collections for RAG
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

# Import embedding function for consistency with RAG
try:
    from app.rag.embeddings import get_embedding_generator
    from app.rag.chromadb_client import ChromaEmbeddingWrapper
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ENRICHED_SOURCES_FILE = PROCESSED_DIR / "enriched_sources.json"
CHROMA_DIR = DATA_DIR / "chroma_db"

# ChromaDB configuration
CHROMADB_HOST = "localhost"
CHROMADB_PORT = 8001  # Docker maps 8001 -> 8000 (memory_store service)

# Collection names
COLLECTIONS = {
    "course_content": "comp237_course_materials",
    "mediasite_video": "comp237_media",
    "youtube_video": "comp237_media",
    "external_resource": "comp237_external",
    "image": "comp237_images",
    "oer": "comp237_oer",
}


class ChromaDBIngestor:
    """Ingests enriched sources into ChromaDB"""
    
    def __init__(self, use_http: bool = False, reset_collections: bool = False):
        """
        Initialize ChromaDB client.
        
        Args:
            use_http: If True, connect to HTTP server. Otherwise, use persistent local DB.
            reset_collections: If True, delete and recreate collections.
        """
        self.use_http = use_http
        self.reset_collections = reset_collections
        
        if use_http:
            try:
                self.client = chromadb.HttpClient(
                    host=CHROMADB_HOST,
                    port=CHROMADB_PORT,
                )
                logger.info(f"Connected to ChromaDB at {CHROMADB_HOST}:{CHROMADB_PORT}")
            except Exception as e:
                logger.warning(f"Could not connect to HTTP ChromaDB: {e}, falling back to local")
                self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        else:
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            logger.info(f"Using persistent ChromaDB at {CHROMA_DIR}")
        
        # Initialize embedding function if available
        self.embedding_fn = None
        if HAS_EMBEDDINGS:
            try:
                embedding_gen = get_embedding_generator()
                self.embedding_fn = ChromaEmbeddingWrapper(embedding_gen.embeddings)
                logger.info("Using Gemini embeddings (768-dim)")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini embeddings: {e}")
                logger.warning("Will use ChromaDB default embeddings (384-dim)")
        
        self.collections: Dict[str, chromadb.Collection] = {}
        self.stats = {
            "ingested": 0,
            "skipped": 0,
            "errors": 0,
            "by_collection": {},
        }
    
    def _get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a collection with proper embedding function"""
        if name not in self.collections:
            # Delete collection if reset requested
            if self.reset_collections:
                try:
                    self.client.delete_collection(name)
                    logger.info(f"Deleted existing collection: {name}")
                except Exception:
                    pass  # Collection doesn't exist
            
            # Create collection with embedding function if available
            if self.embedding_fn:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            logger.info(f"Created/loaded collection: {name}")
        return self.collections[name]
    
    def _prepare_document(self, source: Dict) -> Dict:
        """Prepare a document for ingestion"""
        # Build metadata
        metadata = {
            "type": source.get("type", "unknown"),
            "title": source.get("title", "Untitled")[:500],  # Truncate for metadata limits
            "is_verified": source.get("is_verified", False),
            "quality_score": source.get("quality_score", 0),
        }
        
        # Add optional fields
        if source.get("module"):
            metadata["module"] = source["module"]
        if source.get("week"):
            metadata["week"] = source["week"]
        if source.get("topic"):
            metadata["topic"] = source["topic"][:200]
        if source.get("blackboard_url"):
            metadata["blackboard_url"] = source["blackboard_url"]
        if source.get("external_url"):
            metadata["external_url"] = source["external_url"]
        if source.get("source_file"):
            metadata["source_file"] = source["source_file"][:200]
        if source.get("concepts"):
            metadata["concepts"] = ",".join(source["concepts"][:10])  # Limit concepts
        if source.get("keywords"):
            metadata["keywords"] = ",".join(source["keywords"][:10])
        
        # Image-specific: save path for frontend API
        if source.get("type") == "image" and source.get("source_file"):
            metadata["image_path"] = source["source_file"]
        
        return {
            "id": source["id"],
            "document": source.get("content", ""),
            "metadata": metadata,
        }
    
    def ingest_sources(self, sources: List[Dict]) -> None:
        """Ingest all sources into appropriate collections"""
        logger.info(f"Ingesting {len(sources)} sources...")
        
        # Group sources by collection and deduplicate
        by_collection: Dict[str, Dict[str, Dict]] = {}  # collection -> {id -> source}
        
        for source in sources:
            source_type = source.get("type", "unknown")
            collection_name = COLLECTIONS.get(source_type, "comp237_course_materials")
            
            if collection_name not in by_collection:
                by_collection[collection_name] = {}
            
            # Deduplicate by ID within collection
            source_id = source.get("id", "")
            if source_id and source_id not in by_collection[collection_name]:
                by_collection[collection_name][source_id] = source
            elif source_id:
                self.stats["skipped"] += 1  # Duplicate
        
        # Ingest each collection
        for collection_name, sources_dict in by_collection.items():
            self._ingest_collection(collection_name, list(sources_dict.values()))
    
    def _ingest_collection(self, collection_name: str, sources: List[Dict]) -> None:
        """Ingest sources into a specific collection"""
        logger.info(f"Ingesting {len(sources)} sources into {collection_name}...")
        
        collection = self._get_or_create_collection(collection_name)
        
        # Prepare documents in batches
        batch_size = 100
        docs_ingested = 0
        
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            
            ids = []
            documents = []
            metadatas = []
            
            for source in batch:
                try:
                    prepared = self._prepare_document(source)
                    
                    # Skip empty documents
                    if not prepared["document"].strip():
                        self.stats["skipped"] += 1
                        continue
                    
                    ids.append(prepared["id"])
                    documents.append(prepared["document"])
                    metadatas.append(prepared["metadata"])
                    
                except Exception as e:
                    logger.warning(f"Error preparing document {source.get('id')}: {e}")
                    self.stats["errors"] += 1
            
            # Upsert batch
            if ids:
                try:
                    collection.upsert(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                    )
                    docs_ingested += len(ids)
                except Exception as e:
                    logger.error(f"Error ingesting batch: {e}")
                    self.stats["errors"] += len(ids)
        
        self.stats["ingested"] += docs_ingested
        self.stats["by_collection"][collection_name] = docs_ingested
        logger.info(f"  Ingested {docs_ingested} documents into {collection_name}")
    
    def verify_collections(self) -> Dict:
        """Verify all collections have expected documents"""
        verification = {}
        
        for collection_name in set(COLLECTIONS.values()):
            try:
                collection = self._get_or_create_collection(collection_name)
                count = collection.count()
                verification[collection_name] = {
                    "count": count,
                    "status": "ok" if count > 0 else "empty",
                }
            except Exception as e:
                verification[collection_name] = {
                    "count": 0,
                    "status": f"error: {e}",
                }
        
        return verification
    
    def run(self):
        """Run the full ingestion pipeline"""
        logger.info("Starting ChromaDB ingestion...")
        
        # Load enriched sources
        if not ENRICHED_SOURCES_FILE.exists():
            logger.error(f"Enriched sources file not found: {ENRICHED_SOURCES_FILE}")
            logger.error("Run source_processor.py first")
            return
        
        with open(ENRICHED_SOURCES_FILE, "r") as f:
            data = json.load(f)
        
        sources = data.get("sources", [])
        if not sources:
            logger.error("No sources found in enriched_sources.json")
            return
        
        # Ingest sources
        self.ingest_sources(sources)
        
        # Verify collections
        verification = self.verify_collections()
        
        # Print summary
        self._print_summary(verification)
    
    def _print_summary(self, verification: Dict):
        """Print ingestion summary"""
        print("\n" + "="*60)
        print("CHROMADB INGESTION SUMMARY")
        print("="*60)
        print(f"Total Ingested:    {self.stats['ingested']}")
        print(f"Skipped (empty):   {self.stats['skipped']}")
        print(f"Errors:            {self.stats['errors']}")
        print("-"*40)
        print("\nBy Collection:")
        for name, count in self.stats["by_collection"].items():
            print(f"  {name}: {count}")
        print("-"*40)
        print("\nCollection Verification:")
        for name, info in verification.items():
            status = "✓" if info["status"] == "ok" else "✗"
            print(f"  {status} {name}: {info['count']} documents ({info['status']})")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest enriched sources into ChromaDB")
    parser.add_argument("--http", action="store_true", help="Use HTTP client to connect to ChromaDB server")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate collections (use when changing embedding dimensions)")
    args = parser.parse_args()
    
    ingestor = ChromaDBIngestor(use_http=args.http, reset_collections=args.reset)
    ingestor.run()


if __name__ == "__main__":
    main()
