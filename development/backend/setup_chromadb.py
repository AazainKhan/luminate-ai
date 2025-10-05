"""
ChromaDB Setup for Luminate AI
Purpose: Initialize ChromaDB, load COMP237 content, and generate embeddings

Features:
- Creates persistent ChromaDB collection
- Loads all 593 JSON files from comp_237_content/
- Generates embeddings using sentence-transformers (all-MiniLM-L6-v2)
- Stores metadata: course_id, bb_doc_id, live_url, title, module
- Supports semantic search queries
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from tqdm import tqdm

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
COMP237_DATA = PROJECT_ROOT / "comp_237_content"
CHROMA_DB_PATH = PROJECT_ROOT / "chromadb_data"
LOGS_DIR = PROJECT_ROOT / "development/backend/logs"

# Create directories
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class LuminateChromaDB:
    """ChromaDB manager for Luminate AI"""
    
    def __init__(
        self,
        persist_directory: Path = CHROMA_DB_PATH,
        collection_name: str = "comp237_content",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "COMP237 course content embeddings"}
        )
        
        print(f"✓ ChromaDB initialized at: {self.persist_directory}")
        print(f"✓ Collection: {self.collection_name}")
        print(f"✓ Embedding model: {self.embedding_model}")
        print(f"✓ Current document count: {self.collection.count()}")
    
    def load_json_files(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Load all JSON files from comp_237_content directory"""
        json_files = list(data_dir.rglob("*.json"))
        print(f"\n📁 Found {len(json_files)} JSON files")
        
        documents = []
        for json_file in tqdm(json_files, desc="Loading JSON files"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                documents.append(data)
            except Exception as e:
                print(f"⚠️  Error loading {json_file.name}: {e}")
        
        print(f"✓ Loaded {len(documents)} documents")
        return documents
    
    def prepare_chunks_for_embedding(
        self,
        documents: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
        """
        Prepare chunks for ChromaDB insertion
        
        Returns:
            (ids, texts, metadatas) ready for ChromaDB
        """
        ids = []
        texts = []
        metadatas = []
        
        total_chunks = sum(len(doc.get("chunks", [])) for doc in documents)
        print(f"\n📝 Preparing {total_chunks} chunks for embedding...")
        
        # Track chunk ID uniqueness
        chunk_id_counter = 0
        
        with tqdm(total=total_chunks, desc="Preparing chunks") as pbar:
            for doc in documents:
                course_id = doc.get("course_id", "unknown")
                course_name = doc.get("course_name", "unknown")
                module = doc.get("module", "unknown")
                file_name = doc.get("file_name", "unknown")
                bb_doc_id = doc.get("bb_doc_id")
                live_url = doc.get("live_lms_url")
                title = doc.get("title", "Untitled")
                content_type = doc.get("content_type", "unknown")
                
                for chunk in doc.get("chunks", []):
                    chunk_id = chunk.get("chunk_id")
                    content = chunk.get("content", "")
                    
                    if not chunk_id or not content:
                        continue
                    
                    # Make chunk ID globally unique
                    chunk_id_counter += 1
                    chunk_id = f"{chunk_id}_{chunk_id_counter}"
                    
                    # Prepare metadata
                    metadata = {
                        "course_id": course_id,
                        "course_name": course_name,
                        "module": module,
                        "file_name": file_name,
                        "title": title,
                        "content_type": content_type,
                        "chunk_index": chunk.get("chunk_index", 0),
                        "total_chunks": chunk.get("total_chunks", 1),
                        "token_count": chunk.get("token_count", 0)
                    }
                    
                    # Add BB doc ID and URL if available
                    if bb_doc_id:
                        metadata["bb_doc_id"] = bb_doc_id
                    if live_url:
                        metadata["live_lms_url"] = live_url
                    
                    # Add tags
                    tags = chunk.get("tags", [])
                    if tags:
                        metadata["tags"] = ",".join(tags)
                    
                    ids.append(chunk_id)
                    texts.append(content)
                    metadatas.append(metadata)
                    
                    pbar.update(1)
        
        print(f"✓ Prepared {len(ids)} chunks")
        return ids, texts, metadatas
    
    def upsert_chunks(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Upsert chunks to ChromaDB in batches
        
        Args:
            ids: List of chunk IDs
            documents: List of text content
            metadatas: List of metadata dicts
            batch_size: Number of chunks per batch
        """
        total = len(ids)
        print(f"\n🚀 Upserting {total} chunks to ChromaDB (batch size: {batch_size})...")
        
        for i in tqdm(range(0, total, batch_size), desc="Upserting batches"):
            batch_ids = ids[i:i+batch_size]
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            
            try:
                self.collection.upsert(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_meta
                )
            except Exception as e:
                print(f"\n⚠️  Error upserting batch {i}-{i+batch_size}: {e}")
                # Continue with next batch
        
        final_count = self.collection.count()
        print(f"✓ Upsert complete! Total documents in collection: {final_count}")
    
    def query(
        self,
        query_text: str,
        n_results: int = 10,
        filter_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query ChromaDB for relevant content
        
        Args:
            query_text: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            Query results with documents, metadatas, distances
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        count = self.collection.count()
        
        # Sample some documents to get metadata
        sample = self.collection.peek(limit=100)
        
        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
            "persist_directory": str(self.persist_directory),
            "sample_metadata_keys": list(sample["metadatas"][0].keys()) if sample["metadatas"] else []
        }


def main():
    """Main setup workflow"""
    print("=" * 80)
    print("Luminate AI ChromaDB Setup")
    print("=" * 80)
    
    # Initialize ChromaDB
    chroma_db = LuminateChromaDB()
    
    # Check if collection is already populated
    current_count = chroma_db.collection.count()
    if current_count > 0:
        print(f"\n⚠️  Collection already contains {current_count} documents")
        response = input("Do you want to re-load all data? (yes/no): ").strip().lower()
        if response != "yes":
            print("Skipping data load. Using existing collection.")
            print_stats(chroma_db)
            return
        else:
            print("Clearing collection...")
            chroma_db.client.delete_collection(chroma_db.collection_name)
            chroma_db.collection = chroma_db.client.create_collection(
                name=chroma_db.collection_name,
                embedding_function=chroma_db.embedding_function,
                metadata={"description": "COMP237 course content embeddings"}
            )
    
    # Load JSON files
    documents = chroma_db.load_json_files(COMP237_DATA)
    
    if not documents:
        print("❌ No documents found!")
        sys.exit(1)
    
    # Prepare chunks
    ids, texts, metadatas = chroma_db.prepare_chunks_for_embedding(documents)
    
    if not ids:
        print("❌ No chunks prepared!")
        sys.exit(1)
    
    # Upsert to ChromaDB
    chroma_db.upsert_chunks(ids, texts, metadatas)
    
    # Print statistics
    print_stats(chroma_db)
    
    # Run sample query
    run_sample_queries(chroma_db)


def print_stats(chroma_db: LuminateChromaDB):
    """Print collection statistics"""
    print("\n" + "=" * 80)
    print("ChromaDB Statistics")
    print("=" * 80)
    
    stats = chroma_db.get_stats()
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Collection Name: {stats['collection_name']}")
    print(f"Embedding Model: {stats['embedding_model']}")
    print(f"Persist Directory: {stats['persist_directory']}")
    print(f"Metadata Keys: {', '.join(stats['sample_metadata_keys'])}")
    print("=" * 80)


def run_sample_queries(chroma_db: LuminateChromaDB):
    """Run sample queries to test retrieval"""
    print("\n" + "=" * 80)
    print("Sample Queries")
    print("=" * 80)
    
    sample_queries = [
        "machine learning algorithms",
        "neural networks",
        "search algorithms in AI",
        "course syllabus and schedule"
    ]
    
    for query in sample_queries:
        print(f"\n🔍 Query: '{query}'")
        results = chroma_db.query(query, n_results=3)
        
        if results["documents"] and results["documents"][0]:
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                print(f"\n  Result {i+1} (score: {dist:.4f}):")
                print(f"    Title: {meta.get('title', 'N/A')}")
                print(f"    Module: {meta.get('module', 'N/A')}")
                print(f"    URL: {meta.get('live_lms_url', 'N/A')}")
                print(f"    Excerpt: {doc[:150]}...")
        else:
            print("  No results found")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
