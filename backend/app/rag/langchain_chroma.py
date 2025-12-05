"""
LangChain Chroma wrapper for RAG
This provides better compatibility with embeddings and query operations
"""

from typing import List, Dict, Optional, Tuple
import logging
# Updated import for LangChain 0.2+ compatibility
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.rag.embeddings import get_embedding_generator
from app.rag.chromadb_client import ChromaEmbeddingWrapper
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


class LangChainChromaClient:
    """
    RAG client using LangChain's Chroma wrapper
    Provides better embedding compatibility and simpler query interface
    """
    
    def __init__(self):
        """Initialize LangChain Chroma client"""
        # Get embedding function
        embedding_gen = get_embedding_generator()
        # Wrap it to ensure compatibility with ChromaDB's expectations
        self.embeddings = ChromaEmbeddingWrapper(embedding_gen.embeddings)
        
        # Create ChromaDB HTTP client
        try:
            self.chroma_client = chromadb.HttpClient(
                host=settings.chromadb_host,
                port=settings.chromadb_port,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            # Test connection
            self.chroma_client.heartbeat()
            logger.info(f"Connected to ChromaDB HTTP server at {settings.chromadb_host}:{settings.chromadb_port}")
        except Exception as e:
            logger.warning(f"Could not connect to ChromaDB HTTP server: {e}. Falling back to PersistentClient.")
            self.chroma_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        
        self.collection_name = "comp237_course_materials"
        
        # Initialize LangChain Chroma wrapper
        try:
            self.vectorstore = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            logger.info(f"✅ Connected to Chroma collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Error connecting to Chroma: {e}")
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """Compatibility wrapper (unused but kept for reference)."""
        return self.vectorstore.similarity_search(query=query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Compatibility wrapper for legacy callers."""
        return self.vectorstore.similarity_search_with_score(query=query, k=k, filter=filter)

    def _normalize_document(
        self,
        doc: Document,
        score: float
    ) -> Dict:
        """
        Normalize a LangChain document into a structured record
        """
        metadata = doc.metadata or {}
        preview = doc.page_content.replace("\n", " ").strip()
        if len(preview) > 220:
            preview = preview[:217] + "..."
        
        return {
            "content": doc.page_content,
            "metadata": metadata,
            "relevance_score": float(score),
            "relevance_score": float(score),
            "source_filename": metadata.get("source_filename") or metadata.get("source_file") or metadata.get("title") or "Unknown",
            "chunk_index": metadata.get("chunk_index", 0),
            "content_type": metadata.get("content_type", "unknown"),
            "page": metadata.get("page", metadata.get("page_number", "N/A")),
            "preview": preview,
            "public_url": metadata.get("public_url", ""),
        }
    
    def retrieve_with_metadata(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform similarity search and return structured metadata records
        """
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            structured = [self._normalize_document(doc, score) for doc, score in results]
            logger.info(f"✅ Retrieved {len(structured)} structured documents")
            return structured
        except Exception as e:
            logger.error(f"❌ Error retrieving structured documents: {e}")
            raise
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            count = collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "status": "connected"
            }
        except Exception as e:
            logger.error(f"❌ Error getting collection info: {e}")
            return {"error": str(e)}
    
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the collection
        
        Args:
            documents: List of Document objects
            ids: Optional list of IDs
        """
        try:
            self.vectorstore.add_documents(
                documents=documents,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to collection")
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def summarize_sources(self, records: List[Dict]) -> List[Dict]:
        """
        Summarize retrieval results into unique source cards
        """
        summaries: List[Dict] = []
        seen_files = set()
        
        for record in records:
            filename = record.get("source_filename", "Unknown")
            if filename in seen_files:
                continue
            seen_files.add(filename)
            
            summaries.append({
                "filename": filename,
                "chunk_index": record.get("chunk_index", 0),
                "relevance_score": float(record.get("relevance_score", 0.0)),
                "content_type": record.get("content_type", "unknown"),
                "preview": record.get("preview", ""),
                "public_url": record.get("public_url", ""),
                "page": record.get("page", "N/A")
            })
        
        return summaries


# Global instance
_langchain_chroma_client: Optional[LangChainChromaClient] = None


def get_langchain_chroma_client() -> LangChainChromaClient:
    """Get or create LangChain Chroma client instance"""
    global _langchain_chroma_client
    if _langchain_chroma_client is None:
        _langchain_chroma_client = LangChainChromaClient()
    return _langchain_chroma_client
