import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any
import argparse

from app.rag.chromadb_client import ChromaDBClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddedContentIngester:
    """Ingests embedded content from JSON into ChromaDB"""

    def __init__(self, json_path: str, course_id: str = "COMP237"):
        self.json_path = Path(json_path)
        self.course_id = course_id
        self.chromadb = ChromaDBClient()

    def load_content(self) -> List[Dict[str, Any]]:
        """Load embedded content from JSON file."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_path}")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return data.get("embedded_items", [])

    def process_and_ingest(self):
        """Process items and ingest into ChromaDB."""
        items = self.load_content()
        logger.info(f"Found {len(items)} items to process")
        
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
                
                # Construct informative text for the vector store
                doc_text = (
                    f"Embedded Content Resource: {title}\n"
                    f"Location: {parent}\n"
                    f"Type: {link_type}\n"
                    f"URL: {url}\n"
                    f"Context: {context_text}"
                )
                
                # Construct metadata
                metadata = {
                    "course_id": self.course_id,
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
                ids.append(str(uuid.uuid4()))
        
        if documents:
            logger.info(f"Ingesting {len(documents)} embedded content chunks")
            self.chromadb.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("Ingestion complete")
        else:
            logger.info("No documents to ingest")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Embedded Content into ChromaDB")
    parser.add_argument("--json-path", required=True, help="Path to embedded_content.json")
    parser.add_argument("--course-id", default="COMP237", help="Course ID")
    
    args = parser.parse_args()
    
    ingester = EmbeddedContentIngester(args.json_path, args.course_id)
    ingester.process_and_ingest()
