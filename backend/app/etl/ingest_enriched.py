"""
ChromaDB Ingestion Script for Enriched Sources

Ingests the unified enriched sources into ChromaDB with proper metadata
for intelligent retrieval by the agent.

Features:
- Multi-collection support (course content, media, OER)
- Rich metadata for filtering
- Concept-based indexing
- Deduplication

Usage:
    python -m app.etl.ingest_enriched
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

from app.config import settings as app_settings
from app.rag.embeddings import get_embedding_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ENRICHED_FILE = PROCESSED_DIR / "enriched_sources.json"

# Collection names
MAIN_COLLECTION = "comp237_course_materials"
MEDIA_COLLECTION = "comp237_media"
OER_COLLECTION = "comp237_oer"


class EnrichedIngester:
    """Ingests enriched sources into ChromaDB"""
    
    def __init__(self):
        self.client = self._connect_chromadb()
        self.embeddings = get_embedding_generator()
        
        self.stats = {
            "total_ingested": 0,
            "course_content": 0,
            "media": 0,
            "oer": 0,
            "skipped": 0,
            "errors": 0,
        }
    
    def _connect_chromadb(self):
        """Connect to ChromaDB"""
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
    
    def _get_or_create_collection(self, name: str, description: str):
        """Get or create a ChromaDB collection"""
        try:
            # Try to get existing
            collection = self.client.get_collection(name=name)
            logger.info(f"Using existing collection: {name} ({collection.count()} docs)")
            return collection
        except Exception:
            # Create new
            collection = self.client.create_collection(
                name=name,
                metadata={"description": description, "created": datetime.now().isoformat()}
            )
            logger.info(f"Created new collection: {name}")
            return collection
    
    def _prepare_metadata(self, source: Dict) -> Dict:
        """Prepare metadata for ChromaDB (must be primitive types)"""
        metadata = {
            "type": source.get("type", "unknown"),
            "title": source.get("title", "")[:500],  # Limit title length
            "quality_score": source.get("quality_score", 0),
            "is_verified": source.get("is_verified", False),
        }
        
        # Add optional fields if present
        if source.get("module"):
            metadata["module"] = source["module"]
        
        if source.get("week"):
            metadata["week"] = source["week"]
        
        if source.get("topic"):
            metadata["topic"] = str(source["topic"])
        
        if source.get("blackboard_url"):
            metadata["blackboard_url"] = source["blackboard_url"]
        
        if source.get("external_url"):
            metadata["external_url"] = source["external_url"]
        
        if source.get("source_file"):
            metadata["source_file"] = source["source_file"]
        
        # Convert lists to comma-separated strings (ChromaDB doesn't support lists)
        if source.get("concepts"):
            metadata["concepts"] = ",".join(source["concepts"][:10])  # Limit to 10
        
        if source.get("keywords"):
            metadata["keywords"] = ",".join(str(k) for k in source["keywords"][:10])
        
        return metadata
    
    def _chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split content into chunks for embedding"""
        if not content or len(content) <= chunk_size:
            return [content] if content else []
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                for sep in [". ", "! ", "? ", "\n\n", "\n", " "]:
                    break_point = content.rfind(sep, start + chunk_size // 2, end)
                    if break_point > start:
                        end = break_point + len(sep)
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(content) else end
        
        return chunks
    
    def ingest_sources(self, sources: List[Dict], collection_name: str, description: str):
        """Ingest sources into a specific collection"""
        collection = self._get_or_create_collection(collection_name, description)
        
        # Prepare batches
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for source in sources:
            content = source.get("content", "")
            if not content or len(content.strip()) < 20:
                self.stats["skipped"] += 1
                continue
            
            # Chunk long content
            chunks = self._chunk_content(content)
            
            for i, chunk in enumerate(chunks):
                # Generate unique ID
                chunk_id = f"{source.get('id', '')}_{i}" if len(chunks) > 1 else source.get("id", "")
                if not chunk_id:
                    chunk_id = hashlib.md5(chunk.encode()).hexdigest()[:16]
                
                # Prepare metadata
                metadata = self._prepare_metadata(source)
                metadata["chunk_index"] = i
                metadata["total_chunks"] = len(chunks)
                
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append(metadata)
        
        if not documents:
            logger.warning(f"No documents to ingest into {collection_name}")
            return 0
        
        # Generate embeddings in batches
        batch_size = 50
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_embeddings = self.embeddings.embeddings.embed_documents(batch_docs)
            embeddings.extend(batch_embeddings)
            
            if (i + batch_size) % 200 == 0:
                logger.info(f"  Generated {min(i + batch_size, len(documents))}/{len(documents)} embeddings")
        
        # Upsert into collection
        logger.info(f"Upserting {len(documents)} documents into {collection_name}...")
        
        try:
            # ChromaDB has a limit on batch size
            upsert_batch_size = 100
            for i in range(0, len(documents), upsert_batch_size):
                collection.upsert(
                    ids=ids[i:i + upsert_batch_size],
                    documents=documents[i:i + upsert_batch_size],
                    metadatas=metadatas[i:i + upsert_batch_size],
                    embeddings=embeddings[i:i + upsert_batch_size],
                )
            
            logger.info(f"✅ Ingested {len(documents)} documents into {collection_name}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"❌ Error upserting to {collection_name}: {e}")
            self.stats["errors"] += len(documents)
            return 0
    
    def run(self, clear_existing: bool = False):
        """Run the full ingestion pipeline"""
        logger.info("Starting enriched source ingestion...")
        
        # Load enriched sources
        if not ENRICHED_FILE.exists():
            logger.error(f"Enriched sources file not found: {ENRICHED_FILE}")
            logger.error("Run source_processor.py first to generate enriched_sources.json")
            return
        
        with open(ENRICHED_FILE, "r") as f:
            data = json.load(f)
        
        sources = data.get("sources", [])
        logger.info(f"Loaded {len(sources)} enriched sources")
        
        if clear_existing:
            logger.warning("Clearing existing collections...")
            for name in [MAIN_COLLECTION, MEDIA_COLLECTION, OER_COLLECTION]:
                try:
                    self.client.delete_collection(name)
                    logger.info(f"Deleted collection: {name}")
                except Exception:
                    pass
        
        # Categorize sources
        course_content = [s for s in sources if s.get("type") == "course_content"]
        media = [s for s in sources if s.get("type") in ("mediasite_video", "youtube_video", "image")]
        oer = [s for s in sources if s.get("type") == "oer"]
        external = [s for s in sources if s.get("type") == "external_resource"]
        
        # Ingest into appropriate collections
        # Course content + external resources go to main collection
        main_sources = course_content + external
        count = self.ingest_sources(
            main_sources,
            MAIN_COLLECTION,
            "COMP237 course content and verified external resources"
        )
        self.stats["course_content"] = count
        self.stats["total_ingested"] += count
        
        # Media goes to media collection
        count = self.ingest_sources(
            media,
            MEDIA_COLLECTION,
            "COMP237 media resources - videos and images"
        )
        self.stats["media"] = count
        self.stats["total_ingested"] += count
        
        # OER goes to OER collection  
        count = self.ingest_sources(
            oer,
            OER_COLLECTION,
            "Open Educational Resources supplementing COMP237"
        )
        self.stats["oer"] = count
        self.stats["total_ingested"] += count
        
        self._print_summary()
    
    def _print_summary(self):
        """Print ingestion summary"""
        print("\n" + "="*60)
        print("CHROMADB INGESTION SUMMARY")
        print("="*60)
        print(f"Total Ingested:      {self.stats['total_ingested']}")
        print(f"  Course Content:    {self.stats['course_content']}")
        print(f"  Media:             {self.stats['media']}")
        print(f"  OER:               {self.stats['oer']}")
        print(f"Skipped (too short): {self.stats['skipped']}")
        print(f"Errors:              {self.stats['errors']}")
        print("="*60)
        
        # Show collection stats
        print("\nCollection Statistics:")
        for name in [MAIN_COLLECTION, MEDIA_COLLECTION, OER_COLLECTION]:
            try:
                col = self.client.get_collection(name)
                print(f"  {name}: {col.count()} documents")
            except Exception:
                print(f"  {name}: not found")
        print()


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest enriched sources into ChromaDB")
    parser.add_argument("--clear", action="store_true", help="Clear existing collections before ingesting")
    args = parser.parse_args()
    
    ingester = EnrichedIngester()
    ingester.run(clear_existing=args.clear)


if __name__ == "__main__":
    main()
