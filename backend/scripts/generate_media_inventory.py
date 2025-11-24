#!/usr/bin/env python3
"""
Generate comprehensive media inventory JSON
Maps all media files to course context from imsmanifest.xml
"""

import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import mimetypes
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MediaInventoryGenerator:
    """Generate comprehensive media inventory with course context"""
    
    def __init__(self, raw_data_dir: Path, mappings_path: Optional[Path] = None):
        self.raw_data_dir = raw_data_dir
        self.export_dir = raw_data_dir / "ExportFile_COMP237"
        self.manifest_path = self.export_dir / "imsmanifest.xml"
        
        # Resource mapping from manifest
        self.resource_map = {}
        self.title_map = {}
        
        # Load enhanced mappings if available
        self.enhanced_mappings = None
        if mappings_path and mappings_path.exists():
            with open(mappings_path) as f:
                self.enhanced_mappings = json.load(f)
            logger.info(f"✅ Loaded enhanced mappings: {self.enhanced_mappings['statistics']['total_content_items']} items")
        
    def parse_manifest(self):
        """Parse imsmanifest.xml to build resource-to-title mapping"""
        if not self.manifest_path.exists():
            logger.warning("imsmanifest.xml not found")
            return
        
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            # Build title map from organization structure
            for item in root.findall('.//{*}item'):
                item_id = item.get('identifier')
                identifierref = item.get('identifierref')
                title_elem = item.find('{*}title')
                title = title_elem.text if title_elem is not None else 'Unknown'
                
                if identifierref:
                    self.title_map[identifierref] = {
                        'title': title,
                        'item_id': item_id
                    }
            
            # Build resource map
            for resource in root.findall('.//{*}resource'):
                res_id = resource.get('identifier')
                href = resource.get('href')
                res_type = resource.get('type', 'unknown')
                
                self.resource_map[res_id] = {
                    'href': href,
                    'type': res_type,
                    'title': self.title_map.get(res_id, {}).get('title', 'Unknown')
                }
            
            logger.info(f"Parsed manifest: {len(self.resource_map)} resources, {len(self.title_map)} titles")
        except Exception as e:
            logger.error(f"Error parsing manifest: {e}")
    
    def extract_course_context(self, file_path: Path) -> Dict:
        """Extract course context from file path and manifest"""
        rel_path = str(file_path.relative_to(self.export_dir))
        
        # Try enhanced mappings first
        if self.enhanced_mappings:
            content_map = self.enhanced_mappings.get('content_to_module', {})
            
            # Look for resource ID in path
            parts = rel_path.split('/')
            for part in parts:
                if part.startswith('res'):
                    res_id = part.split('.')[0]
                    if res_id in content_map:
                        ctx = content_map[res_id]
                        
                        # Extract module number from parent_title or title
                        module = ctx.get('module', 'Unknown')
                        week = ctx.get('week')
                        title = ctx.get('title', file_path.stem)
                        parent_title = ctx.get('parent_title', '')
                        
                        # Try to extract module from parent title if not in module field
                        if module == 'Unknown' and ('Module' in parent_title or 'Module' in title):
                            import re
                            text_to_search = parent_title if 'Module' in parent_title else title
                            match = re.search(r'Module\s+(\d+)', text_to_search, re.IGNORECASE)
                            if match:
                                module_num = int(match.group(1))
                                module = f"Module {module_num}"
                                week = module_num
                        
                        return {
                            'module': module,
                            'topic': title,
                            'week': week,
                            'title': title,
                            'parent_title': parent_title,
                            'path_context': rel_path
                        }
        
        # Fallback to original logic
        parts = rel_path.split('/')
        module = None
        week = None
        topic = None
        
        # Look for resource ID in path
        for part in parts:
            if part.startswith('res'):
                res_id = part.split('.')[0]
                if res_id in self.resource_map:
                    title = self.resource_map[res_id]['title']
                    
                    # Extract module number from title
                    if 'Module' in title or 'module' in title:
                        try:
                            import re
                            match = re.search(r'Module\s+(\d+)', title, re.IGNORECASE)
                            if match:
                                module_num = int(match.group(1))
                                module = f"Module {module_num}"
                                week = module_num
                        except:
                            pass
                    
                    topic = title
                    break
        
        return {
            'module': module or 'Unknown',
            'topic': topic or file_path.stem,
            'week': week,
            'title': topic or file_path.stem,
            'path_context': rel_path
        }
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except:
            return 0
    
    def get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'unknown'
    
    def process_videos(self) -> List[Dict]:
        """Process all video files"""
        videos = []
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        
        logger.info("Scanning for video files...")
        video_files = []
        for ext in video_extensions:
            video_files.extend(self.export_dir.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(video_files)} video files")
        
        for idx, video_path in enumerate(video_files, 1):
            context = self.extract_course_context(video_path)
            rel_path = str(video_path.relative_to(self.raw_data_dir.parent))
            
            video_data = {
                'id': f'video_{idx:03d}',
                'filename': video_path.name,
                'path': rel_path,
                'size_bytes': self.get_file_size(video_path),
                'mime_type': self.get_mime_type(video_path),
                'course_context': context,
                'transcription': {
                    'status': 'pending',
                    'transcript_path': None,
                    'method': 'whisper_api',
                    'notes': 'Requires manual transcription or API integration'
                },
                'metadata': {
                    'duration_seconds': None,
                    'format': video_path.suffix[1:],
                    'resolution': None,
                    'codec': None
                }
            }
            videos.append(video_data)
        
        return videos
    
    def process_images(self) -> List[Dict]:
        """Process all image files"""
        images = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp']
        
        logger.info("Scanning for image files...")
        image_files = []
        for ext in image_extensions:
            image_files.extend(self.export_dir.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(image_files)} image files")
        
        for idx, image_path in enumerate(image_files, 1):
            context = self.extract_course_context(image_path)
            rel_path = str(image_path.relative_to(self.raw_data_dir.parent))
            
            image_data = {
                'id': f'image_{idx:03d}',
                'filename': image_path.name,
                'path': rel_path,
                'size_bytes': self.get_file_size(image_path),
                'mime_type': self.get_mime_type(image_path),
                'course_context': context,
                'ocr': {
                    'status': 'pending',
                    'extracted_text': None,
                    'method': 'tesseract',
                    'notes': 'OCR can extract text from diagrams and screenshots'
                },
                'metadata': {
                    'format': image_path.suffix[1:],
                    'dimensions': None
                }
            }
            images.append(image_data)
        
        return images
    
    def process_documents(self) -> List[Dict]:
        """Process all document files"""
        documents = []
        doc_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.doc', '.ppt', '.xls', '.txt']
        
        logger.info("Scanning for document files...")
        doc_files = []
        for ext in doc_extensions:
            doc_files.extend(self.export_dir.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(doc_files)} document files")
        
        for idx, doc_path in enumerate(doc_files, 1):
            context = self.extract_course_context(doc_path)
            rel_path = str(doc_path.relative_to(self.raw_data_dir.parent))
            
            doc_data = {
                'id': f'document_{idx:03d}',
                'filename': doc_path.name,
                'path': rel_path,
                'size_bytes': self.get_file_size(doc_path),
                'mime_type': self.get_mime_type(doc_path),
                'course_context': context,
                'processing': {
                    'status': 'pending',
                    'ingested_to_chromadb': False,
                    'chunk_count': 0
                },
                'metadata': {
                    'format': doc_path.suffix[1:],
                    'page_count': None
                }
            }
            documents.append(doc_data)
        
        return documents
    
    def process_audio(self) -> List[Dict]:
        """Process all audio files"""
        audio = []
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']
        
        logger.info("Scanning for audio files...")
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(self.export_dir.rglob(f'*{ext}'))
        
        logger.info(f"Found {len(audio_files)} audio files")
        
        for idx, audio_path in enumerate(audio_files, 1):
            context = self.extract_course_context(audio_path)
            rel_path = str(audio_path.relative_to(self.raw_data_dir.parent))
            
            audio_data = {
                'id': f'audio_{idx:03d}',
                'filename': audio_path.name,
                'path': rel_path,
                'size_bytes': self.get_file_size(audio_path),
                'mime_type': self.get_mime_type(audio_path),
                'course_context': context,
                'transcription': {
                    'status': 'pending',
                    'transcript_path': None,
                    'method': 'whisper_api'
                },
                'metadata': {
                    'duration_seconds': None,
                    'format': audio_path.suffix[1:],
                    'bitrate': None
                }
            }
            audio.append(audio_data)
        
        return audio
    
    def generate_inventory(self) -> Dict:
        """Generate complete media inventory"""
        logger.info("="*80)
        logger.info("GENERATING COMPREHENSIVE MEDIA INVENTORY")
        logger.info("="*80)
        
        # Parse manifest first
        self.parse_manifest()
        
        # Process all media types
        videos = self.process_videos()
        images = self.process_images()
        documents = self.process_documents()
        audio = self.process_audio()
        
        # Count total files
        total_files = len(list(self.export_dir.rglob('*')))
        
        inventory = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'course_id': 'COMP237',
            'course_title': 'Introduction to Artificial Intelligence',
            'export_source': 'Blackboard Learn',
            'summary': {
                'total_files': total_files,
                'videos': len(videos),
                'images': len(images),
                'documents': len(documents),
                'audio': len(audio),
                'total_media': len(videos) + len(images) + len(audio)
            },
            'videos': videos,
            'images': images,
            'documents': documents,
            'audio': audio,
            'processing_notes': {
                'videos': 'Require transcription via Whisper API or manual input',
                'images': 'Can be processed with OCR (Tesseract) to extract text from diagrams',
                'documents': 'Can be ingested into ChromaDB for RAG',
                'audio': 'Require transcription if present'
            },
            'next_steps': [
                'Transcribe videos using OpenAI Whisper API',
                'Run OCR on images to extract diagram text',
                'Ingest all documents into ChromaDB',
                'Link media references to course modules in agent responses'
            ]
        }
        
        return inventory


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "raw_data"
    output_dir = project_root / "backend" / "cleaned_data"
    mappings_path = output_dir / "blackboard_mappings.json"
    
    if not raw_data_dir.exists():
        logger.error(f"raw_data directory not found: {raw_data_dir}")
        return 1
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate inventory with enhanced mappings
    generator = MediaInventoryGenerator(raw_data_dir, mappings_path)
    inventory = generator.generate_inventory()
    
    # Save to JSON
    output_path = output_dir / "media_inventory.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    logger.info("="*80)
    logger.info("INVENTORY GENERATION COMPLETE")
    logger.info("="*80)
    logger.info(f"\nSummary:")
    logger.info(f"  Total Files: {inventory['summary']['total_files']}")
    logger.info(f"  Videos: {inventory['summary']['videos']}")
    logger.info(f"  Images: {inventory['summary']['images']}")
    logger.info(f"  Documents: {inventory['summary']['documents']}")
    logger.info(f"  Audio: {inventory['summary']['audio']}")
    logger.info(f"\nOutput saved to: {output_path}")
    logger.info(f"\nNext Steps:")
    for step in inventory['next_steps']:
        logger.info(f"  - {step}")
    
    return 0


if __name__ == "__main__":
    exit(main())

