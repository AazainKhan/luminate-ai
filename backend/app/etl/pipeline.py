"""
ETL Pipeline Orchestration
Coordinates parsing, processing, and vectorization
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging
import uuid

from app.etl.blackboard_parser import BlackboardParser
from app.etl.file_discovery import FileDiscovery, discover_course_files
from app.etl.document_processor import DocumentProcessor, process_documents
from app.rag.chromadb_client import get_chromadb_client
from app.rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Orchestrates the ETL process"""

    def __init__(self):
        """Initialize ETL pipeline"""
        self.chromadb = get_chromadb_client()
        self.embedding_generator = get_embedding_generator()
        self.document_processor = DocumentProcessor()

    def process_blackboard_export(
        self,
        zip_path: Path,
        output_dir: Path,
        course_id: str = "COMP237"
    ) -> Dict[str, any]:
        """
        Process a Blackboard export ZIP file
        
        Args:
            zip_path: Path to Blackboard export ZIP
            output_dir: Directory to extract files to
            course_id: Course identifier
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Step 1: Parse manifest
            logger.info(f"Parsing Blackboard export: {zip_path}")
            parser = BlackboardParser(zip_path)
            manifest_data = parser.parse_manifest()
            
            # Step 2: Extract files
            logger.info(f"Extracting files to: {output_dir}")
            extracted_files = parser.extract_files(output_dir)
            
            # Step 3: Discover files
            logger.info("Discovering course files")
            file_discovery = FileDiscovery(output_dir)
            discovered_files = file_discovery.discover_files()
            
            # Filter to processable files (PDFs, documents)
            processable_files = [
                f for f in discovered_files
                if f['type'] in ['pdf', 'word', 'text']
            ]
            
            # Step 4: Process documents
            logger.info(f"Processing {len(processable_files)} files")
            chunks = process_documents(
                processable_files,
                course_id=course_id,
                processor=self.document_processor
            )
            
            # Step 5: Generate embeddings and store
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            self._ingest_chunks(chunks)
            
            return {
                "status": "success",
                "manifest_resources": len(manifest_data.get("resources", {})),
                "files_discovered": len(discovered_files),
                "files_processed": len(processable_files),
                "chunks_created": len(chunks),
                "chunks_ingested": len(chunks),
            }
        except Exception as e:
            logger.error(f"Error in ETL pipeline: {e}")
            raise

    def process_directory(
        self,
        directory_path: Path,
        course_id: str = "COMP237"
    ) -> Dict[str, any]:
        """
        Process files from a directory (for pre-loaded data)
        
        Args:
            directory_path: Directory containing course files
            course_id: Course identifier
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Discover files
            logger.info(f"Discovering files in: {directory_path}")
            file_data = discover_course_files(directory_path)
            
            # Filter to processable files
            processable_files = [
                f for f in file_data['all_files']
                if f['type'] in ['pdf', 'word', 'text']
            ]
            
            # Process documents
            logger.info(f"Processing {len(processable_files)} files")
            chunks = process_documents(
                processable_files,
                course_id=course_id,
                processor=self.document_processor
            )
            
            # Generate embeddings and store
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            self._ingest_chunks(chunks)
            
            return {
                "status": "success",
                "files_discovered": len(file_data['all_files']),
                "files_processed": len(processable_files),
                "chunks_created": len(chunks),
                "chunks_ingested": len(chunks),
            }
        except Exception as e:
            logger.error(f"Error processing directory: {e}")
            raise

    def _ingest_chunks(self, chunks: List[Dict[str, any]]):
        """
        Generate embeddings and ingest chunks into ChromaDB
        
        Args:
            chunks: List of chunk dictionaries
        """
        if not chunks:
            logger.warning("No chunks to ingest")
            return
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add to ChromaDB
        self.chromadb.add_documents(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        
        logger.info(f"Ingested {len(chunks)} chunks into ChromaDB")


def run_etl_pipeline(
    source_path: Path,
    output_dir: Optional[Path] = None,
    course_id: str = "COMP237"
) -> Dict[str, any]:
    """
    Convenience function to run ETL pipeline
    
    Args:
        source_path: Path to ZIP file or directory
        output_dir: Optional output directory for extraction
        course_id: Course identifier
        
    Returns:
        Processing results
    """
    pipeline = ETLPipeline()
    
    if source_path.suffix.lower() == '.zip':
        if not output_dir:
            output_dir = source_path.parent / f"{source_path.stem}_extracted"
        return pipeline.process_blackboard_export(source_path, output_dir, course_id)
    else:
        return pipeline.process_directory(source_path, course_id)

