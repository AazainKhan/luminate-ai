"""
LangChain Chroma wrapper for RAG
This provides better compatibility with embeddings and query operations
"""

from typing import List, Dict, Optional, Tuple
import logging
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.rag.embeddings import get_embedding_generator
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
        self.embeddings = embedding_gen.embeddings
        
        # Create ChromaDB HTTP client
        self.chroma_client = chromadb.HttpClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
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
        """
        Perform similarity search
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of Document objects with page_content and metadata
        """
        try:
            docs = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            logger.info(f"✅ Retrieved {len(docs)} documents for query")
            return docs
        except Exception as e:
            logger.error(f"❌ Error in similarity search: {e}")
            raise
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search with relevance scores
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (Document, score) tuples
        """
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            logger.info(f"✅ Retrieved {len(results)} documents with scores")
            return results
        except Exception as e:
            logger.error(f"❌ Error in similarity search with score: {e}")
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
    
    def format_results_for_agent(
        self,
        results: List[Tuple[Document, float]]
    ) -> Tuple[List[str], List[Dict]]:
        """
        Format search results for agent consumption
        
        Args:
            results: List of (Document, score) tuples
            
        Returns:
            Tuple of (contexts, sources)
        """
        contexts = []
        sources = []
        
        for doc, score in results:
            contexts.append(doc.page_content)
            
            # Extract source information from metadata
            metadata = doc.metadata
            source_info = {
                "filename": metadata.get("source_filename", "Unknown"),
                "page": metadata.get("page", "N/A"),
                "chunk_index": metadata.get("chunk_index", 0),
                "relevance_score": float(score),
                "content_type": metadata.get("content_type", "unknown")
            }
            sources.append(source_info)
        
        return contexts, sources


# Global instance
_langchain_chroma_client: Optional[LangChainChromaClient] = None


def get_langchain_chroma_client() -> LangChainChromaClient:
    """Get or create LangChain Chroma client instance"""
    global _langchain_chroma_client
    if _langchain_chroma_client is None:
        _langchain_chroma_client = LangChainChromaClient()
    return _langchain_chroma_client

