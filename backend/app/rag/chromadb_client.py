"""
ChromaDB client for vector storage
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from app.config import settings

from app.rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class ChromaEmbeddingWrapper:
    """Wrapper to make LangChain embeddings compatible with ChromaDB"""
    def __init__(self, langchain_embeddings):
        self.langchain_embeddings = langchain_embeddings
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        # logger.info(f"Embedding input type: {type(input)}")
        if isinstance(input, str):
            input = [input]
        return self.langchain_embeddings.embed_documents(input)
        
    def embed_query(self, input: str) -> List[float]:
        if isinstance(input, list):
            return self.langchain_embeddings.embed_documents(input)
        return self.langchain_embeddings.embed_query(input)
        
    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.langchain_embeddings.embed_documents(input)
        
    def name(self) -> str:
        return "gemini_embeddings"

class ChromaDBClient:
    """Client for interacting with ChromaDB"""

    def __init__(self):
        """Initialize ChromaDB client"""
        try:
            self.client = chromadb.HttpClient(
                host=settings.chromadb_host,
                port=settings.chromadb_port,
                settings=Settings(anonymized_telemetry=False)
            )
            # Test connection
            self.client.heartbeat()
            logger.info(f"Connected to ChromaDB HTTP server at {settings.chromadb_host}:{settings.chromadb_port}")
        except Exception as e:
            logger.warning(f"Could not connect to ChromaDB HTTP server: {e}. Falling back to PersistentClient.")
            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False)
            )
            
        self.collection_name = "comp237_course_materials"
        self.collection = None
        # Wrap the LangChain embedding generator
        lc_embeddings = get_embedding_generator().embeddings
        self.embedding_function = ChromaEmbeddingWrapper(lc_embeddings)
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists, create if not"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "COMP 237 course materials"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Connected to collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to the collection
        
        Args:
            documents: List of document text content
            metadatas: List of metadata dictionaries
            ids: List of unique IDs for each document
            embeddings: Optional list of embedding vectors
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            logger.info(f"Added {len(documents)} documents to collection")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with ids, documents, metadatas, distances
        """
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            raise

    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}

    def delete_collection(self):
        """Delete the collection (use with caution)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.warning(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise


# Global client instance
_chromadb_client: Optional[ChromaDBClient] = None


def get_chromadb_client() -> ChromaDBClient:
    """Get or create ChromaDB client instance"""
    global _chromadb_client
    if _chromadb_client is None:
        _chromadb_client = ChromaDBClient()
    return _chromadb_client

