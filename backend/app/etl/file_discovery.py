"""
File Discovery for Blackboard Exports
Extracts and discovers PDFs, documents, and course materials
"""

from pathlib import Path
from typing import List, Dict, Optional
import zipfile
import logging

logger = logging.getLogger(__name__)


class FileDiscovery:
    """Discovers and categorizes files from Blackboard exports"""

    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.doc': 'word',
        '.docx': 'word',
        '.ppt': 'powerpoint',
        '.pptx': 'powerpoint',
        '.xls': 'excel',
        '.xlsx': 'excel',
        '.txt': 'text',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
    }

    def __init__(self, base_path: Path):
        """
        Initialize file discovery
        
        Args:
            base_path: Base directory to search for files
        """
        self.base_path = Path(base_path)

    def discover_files(self, pattern: str = "**/*") -> List[Dict[str, any]]:
        """
        Discover all supported files in the base path
        
        Args:
            pattern: Glob pattern to search (default: all files)
            
        Returns:
            List of file information dictionaries
        """
        discovered_files = []
        
        for file_path in self.base_path.rglob(pattern):
            if not file_path.is_file():
                continue
            
            # Skip system files
            if self._is_system_file(file_path):
                continue
            
            # Check if file type is supported
            file_type = self._get_file_type(file_path)
            if not file_type:
                continue
            
            file_info = {
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_path)),
                "name": file_path.name,
                "extension": file_path.suffix.lower(),
                "type": file_type,
                "size": file_path.stat().st_size,
            }
            
            discovered_files.append(file_info)
            logger.debug(f"Discovered: {file_info['relative_path']} ({file_type})")
        
        logger.info(f"Discovered {len(discovered_files)} files")
        return discovered_files

    def _is_system_file(self, file_path: Path) -> bool:
        """Check if file is a system file to skip"""
        name = file_path.name.lower()
        return (
            name.startswith('.') or
            name == 'thumbs.db' or
            '__macosx' in str(file_path).lower() or
            '.ds_store' in name
        )

    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """Get file type category"""
        ext = file_path.suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(ext)

    def categorize_files(self, files: List[Dict[str, any]]) -> Dict[str, List[Dict[str, any]]]:
        """
        Categorize files by type
        
        Args:
            files: List of file info dictionaries
            
        Returns:
            Dictionary mapping file types to lists of files
        """
        categorized = {}
        
        for file_info in files:
            file_type = file_info['type']
            if file_type not in categorized:
                categorized[file_type] = []
            categorized[file_type].append(file_info)
        
        return categorized

    def find_pdfs(self) -> List[Dict[str, any]]:
        """Find all PDF files"""
        return [
            f for f in self.discover_files()
            if f['type'] == 'pdf'
        ]

    def find_documents(self) -> List[Dict[str, any]]:
        """Find all document files (Word, PowerPoint, etc.)"""
        doc_types = ['word', 'powerpoint', 'excel', 'text']
        return [
            f for f in self.discover_files()
            if f['type'] in doc_types
        ]

    def find_images(self) -> List[Dict[str, any]]:
        """Find all image files"""
        return [
            f for f in self.discover_files()
            if f['type'] == 'image'
        ]


def discover_course_files(base_path: Path) -> Dict[str, any]:
    """
    Convenience function to discover all course files
    
    Args:
        base_path: Base directory containing course files
        
    Returns:
        Dictionary with categorized file information
    """
    discovery = FileDiscovery(base_path)
    all_files = discovery.discover_files()
    categorized = discovery.categorize_files(all_files)
    
    return {
        "all_files": all_files,
        "categorized": categorized,
        "pdfs": discovery.find_pdfs(),
        "documents": discovery.find_documents(),
        "images": discovery.find_images(),
    }

