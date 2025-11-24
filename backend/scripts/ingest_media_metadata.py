#!/usr/bin/env python3
"""
Ingest Media Metadata into ChromaDB
Adds video, image, and document metadata to the vector store for agent reference
"""

import sys
import json
from pathlib import Path
import logging
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chromadb_client import get_chromadb_client
from app.rag.embeddings import get_embedding_generator

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MediaMetadataIngester:
    """Ingests media metadata into ChromaDB"""
    
    def __init__(self):
        self.chromadb = get_chromadb_client()
        self.embedding_generator = get_embedding_generator()
    
    def ingest_media_inventory(self, inventory_path: Path, mappings_path: Path):
        """
        Ingest media inventory into ChromaDB
        
        Args:
            inventory_path: Path to media_inventory.json
            mappings_path: Path to blackboard_mappings.json
        """
        logger.info("="*80)
        logger.info("INGESTING MEDIA METADATA INTO CHROMADB")
        logger.info("="*80)
        
        # Load inventory
        with open(inventory_path, 'r', encoding='utf-8') as f:
            inventory = json.load(f)
        
        # Load mappings for enhanced context
        with open(mappings_path, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        content_map = mappings.get('content_to_module', {})
        
        # Ingest videos
        logger.info("\n📹 Ingesting video metadata...")
        video_chunks = self._create_video_chunks(inventory['videos'], content_map)
        self._ingest_chunks(video_chunks)
        
        # Ingest images (sample - full ingestion after OCR)
        logger.info("\n🖼️ Ingesting image metadata...")
        image_chunks = self._create_image_chunks(inventory['images'], content_map)
        self._ingest_chunks(image_chunks)
        
        # Ingest documents
        logger.info("\n📄 Ingesting document metadata...")
        document_chunks = self._create_document_chunks(inventory['documents'], content_map)
        self._ingest_chunks(document_chunks)
        
        logger.info("\n" + "="*80)
        logger.info("✅ MEDIA METADATA INGESTION COMPLETE")
        logger.info("="*80)
        logger.info(f"\nIngested:")
        logger.info(f"  - Videos: {len(video_chunks)} entries")
        logger.info(f"  - Images: {len(image_chunks)} entries")
        logger.info(f"  - Documents: {len(document_chunks)} entries")
        logger.info(f"  - Total: {len(video_chunks) + len(image_chunks) + len(document_chunks)} entries")
    
    def _create_video_chunks(self, videos: list, content_map: dict) -> list:
        """Create text chunks for video metadata"""
        chunks = []
        
        for video in videos:
            context = video.get('course_context', {})
            module = context.get('module', 'Unknown')
            title = context.get('title', video['filename'])
            parent_title = context.get('parent_title', '')
            week = context.get('week')
            
            # Create descriptive text for embedding
            text_parts = [
                f"Video: {video['filename']}",
                f"Module: {module}",
            ]
            
            if week:
                text_parts.append(f"Week: {week}")
            
            if parent_title and parent_title != title:
                text_parts.append(f"Topic: {parent_title}")
            
            if title != video['filename']:
                text_parts.append(f"Title: {title}")
            
            # Add context from path
            if 'path_context' in context:
                text_parts.append(f"Location: {context['path_context']}")
            
            # Add transcription status
            transcription_status = video.get('transcription_status', 'pending')
            text_parts.append(f"Transcription: {transcription_status}")
            
            # If transcription exists, add it
            if transcription_status == 'completed' and 'transcription_path' in video:
                transcript_path = Path(video['transcription_path'])
                if transcript_path.exists():
                    with open(transcript_path, 'r', encoding='utf-8') as f:
                        transcript = f.read()
                        text_parts.append(f"Transcript: {transcript[:500]}...")  # First 500 chars
            
            text = "\n".join(text_parts)
            
            metadata = {
                'course_id': 'COMP237',
                'content_type': 'video',
                'media_type': 'video',
                'filename': video['filename'],
                'file_path': video['path'],
                'module': module,
                'week_number': str(week) if week else 'unknown',
                'topic': parent_title or title,
                'transcription_status': transcription_status,
            }
            
            chunks.append({
                'text': text,
                'metadata': metadata
            })
        
        logger.info(f"Created {len(chunks)} video metadata chunks")
        return chunks
    
    def _create_image_chunks(self, images: list, content_map: dict) -> list:
        """Create text chunks for image metadata (sample only)"""
        chunks = []
        
        # Only ingest images with known context (not "Unknown")
        relevant_images = [img for img in images if img['course_context']['module'] != 'Unknown']
        
        # Sample: Take first 50 images with context
        sample_images = relevant_images[:50]
        
        for image in sample_images:
            context = image.get('course_context', {})
            module = context.get('module', 'Unknown')
            title = context.get('title', image['filename'])
            parent_title = context.get('parent_title', '')
            week = context.get('week')
            
            # Create descriptive text
            text_parts = [
                f"Image: {image['filename']}",
                f"Module: {module}",
            ]
            
            if week:
                text_parts.append(f"Week: {week}")
            
            if parent_title and parent_title != title:
                text_parts.append(f"Topic: {parent_title}")
            
            if title != image['filename']:
                text_parts.append(f"Title: {title}")
            
            # Add OCR status
            ocr_status = image.get('ocr_status', 'pending')
            text_parts.append(f"OCR: {ocr_status}")
            
            # If OCR exists, add it
            if ocr_status == 'completed' and 'ocr_text_path' in image:
                ocr_path = Path(image['ocr_text_path'])
                if ocr_path.exists():
                    with open(ocr_path, 'r', encoding='utf-8') as f:
                        ocr_text = f.read()
                        text_parts.append(f"Image text: {ocr_text[:300]}...")  # First 300 chars
            
            text = "\n".join(text_parts)
            
            metadata = {
                'course_id': 'COMP237',
                'content_type': 'image',
                'media_type': 'image',
                'filename': image['filename'],
                'file_path': image['path'],
                'module': module,
                'week_number': str(week) if week else 'unknown',
                'topic': parent_title or title,
                'ocr_status': ocr_status,
            }
            
            chunks.append({
                'text': text,
                'metadata': metadata
            })
        
        logger.info(f"Created {len(chunks)} image metadata chunks (sample of {len(relevant_images)} total)")
        return chunks
    
    def _create_document_chunks(self, documents: list, content_map: dict) -> list:
        """Create text chunks for document metadata"""
        chunks = []
        
        for doc in documents:
            context = doc.get('course_context', {})
            module = context.get('module', 'Unknown')
            title = context.get('title', doc['filename'])
            parent_title = context.get('parent_title', '')
            week = context.get('week')
            
            # Create descriptive text
            text_parts = [
                f"Document: {doc['filename']}",
                f"Module: {module}",
            ]
            
            if week:
                text_parts.append(f"Week: {week}")
            
            if parent_title and parent_title != title:
                text_parts.append(f"Topic: {parent_title}")
            
            if title != doc['filename']:
                text_parts.append(f"Title: {title}")
            
            text = "\n".join(text_parts)
            
            metadata = {
                'course_id': 'COMP237',
                'content_type': 'document_reference',
                'media_type': 'document',
                'filename': doc['filename'],
                'file_path': doc['path'],
                'module': module,
                'week_number': str(week) if week else 'unknown',
                'topic': parent_title or title,
            }
            
            chunks.append({
                'text': text,
                'metadata': metadata
            })
        
        logger.info(f"Created {len(chunks)} document metadata chunks")
        return chunks
    
    def _ingest_chunks(self, chunks: list):
        """Ingest chunks into ChromaDB"""
        if not chunks:
            logger.warning("No chunks to ingest")
            return
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Add to ChromaDB
        logger.info(f"Adding {len(chunks)} chunks to ChromaDB...")
        self.chromadb.add_documents(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✅ Ingested {len(chunks)} chunks")


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent
    cleaned_data_dir = project_root / "backend" / "cleaned_data"
    
    inventory_path = cleaned_data_dir / "media_inventory.json"
    mappings_path = cleaned_data_dir / "blackboard_mappings.json"
    
    if not inventory_path.exists():
        logger.error(f"❌ Media inventory not found: {inventory_path}")
        return 1
    
    if not mappings_path.exists():
        logger.error(f"❌ Blackboard mappings not found: {mappings_path}")
        return 1
    
    # Ingest media metadata
    ingester = MediaMetadataIngester()
    ingester.ingest_media_inventory(inventory_path, mappings_path)
    
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS")
    logger.info("="*80)
    logger.info("1. Transcribe videos using OpenAI Whisper API")
    logger.info("2. Run OCR on images to extract diagram text")
    logger.info("3. Re-run this script to ingest transcripts and OCR text")
    logger.info("4. Test agent responses with media references")
    
    return 0


if __name__ == "__main__":
    exit(main())

