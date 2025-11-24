"""
Blackboard Export Parser
Parses imsmanifest.xml to map resource IDs to human-readable titles
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import zipfile
import logging

logger = logging.getLogger(__name__)


class BlackboardParser:
    """Parser for Blackboard export ZIP files"""

    def __init__(self, zip_path: Path):
        """
        Initialize parser with Blackboard export ZIP
        
        Args:
            zip_path: Path to the Blackboard export ZIP file
        """
        self.zip_path = Path(zip_path)
        if not self.zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        self.resource_map: Dict[str, str] = {}
        self.file_map: Dict[str, str] = {}  # Maps resource IDs to file paths
        self.organization_map: Dict[str, List[str]] = {}  # Maps organization items to resources

    def parse_manifest(self) -> Dict[str, any]:
        """
        Parse imsmanifest.xml from the ZIP file
        
        Returns:
            Dictionary containing parsed manifest data
        """
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # Find imsmanifest.xml
                manifest_files = [f for f in zip_ref.namelist() if f.endswith('imsmanifest.xml')]
                
                if not manifest_files:
                    raise ValueError("imsmanifest.xml not found in ZIP file")
                
                manifest_path = manifest_files[0]
                
                # Read and parse XML
                with zip_ref.open(manifest_path) as manifest_file:
                    tree = ET.parse(manifest_file)
                    root = tree.getroot()
                    
                    # Parse resources
                    self._parse_resources(root)
                    
                    # Parse organizations
                    self._parse_organizations(root)
                    
                    return {
                        "resources": self.resource_map,
                        "file_map": self.file_map,
                        "organizations": self.organization_map,
                    }
        except Exception as e:
            logger.error(f"Error parsing manifest: {e}")
            raise

    def _parse_resources(self, root: ET.Element):
        """Parse resources section of manifest"""
        # Find resources element (handle different namespaces)
        ns = {'ims': 'http://www.imsglobal.org/xsd/imscp_v1p1'}
        
        resources_elem = root.find('.//ims:resources', ns)
        if resources_elem is None:
            # Try without namespace
            resources_elem = root.find('.//resources')
        
        if resources_elem is None:
            logger.warning("No resources element found")
            return
        
        for resource in resources_elem.findall('.//resource'):
            # Get resource attributes
            identifier = resource.get('identifier')
            file_attr = resource.get('{http://www.blackboard.com/content-packaging/}file')
            title_attr = resource.get('{http://www.blackboard.com/content-packaging/}title')
            type_attr = resource.get('type')
            
            if identifier:
                # Store resource mapping
                if title_attr:
                    self.resource_map[identifier] = title_attr
                elif identifier:
                    self.resource_map[identifier] = identifier
                
                # Store file mapping
                if file_attr:
                    self.file_map[identifier] = file_attr
                
                logger.debug(f"Resource: {identifier} -> {title_attr or identifier} ({file_attr})")

    def _parse_organizations(self, root: ET.Element):
        """Parse organizations section to understand course structure"""
        ns = {'ims': 'http://www.imsglobal.org/xsd/imscp_v1p1'}
        
        organizations_elem = root.find('.//ims:organizations', ns)
        if organizations_elem is None:
            organizations_elem = root.find('.//organizations')
        
        if organizations_elem is None:
            logger.warning("No organizations element found")
            return
        
        for org in organizations_elem.findall('.//organization'):
            org_id = org.get('identifier')
            if not org_id:
                continue
            
            items = []
            for item in org.findall('.//item'):
                item_id = item.get('identifier')
                identifierref = item.get('identifierref')
                title_elem = item.find('title')
                title = title_elem.text if title_elem is not None else None
                
                if identifierref:
                    items.append({
                        "id": item_id,
                        "resource_ref": identifierref,
                        "title": title,
                    })
            
            if items:
                self.organization_map[org_id] = items

    def extract_files(self, output_dir: Path) -> List[Path]:
        """
        Extract relevant files from ZIP to output directory
        
        Args:
            output_dir: Directory to extract files to
            
        Returns:
            List of extracted file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # Extract all files
                for member in zip_ref.namelist():
                    # Skip system files
                    if '__MACOSX' in member or '.DS_Store' in member:
                        continue
                    
                    # Extract file
                    zip_ref.extract(member, output_dir)
                    extracted_path = output_dir / member
                    
                    if extracted_path.is_file():
                        extracted_files.append(extracted_path)
                
                logger.info(f"Extracted {len(extracted_files)} files to {output_dir}")
                return extracted_files
        except Exception as e:
            logger.error(f"Error extracting files: {e}")
            raise

    def get_resource_title(self, resource_id: str) -> Optional[str]:
        """Get human-readable title for a resource ID"""
        return self.resource_map.get(resource_id)

    def get_resource_file(self, resource_id: str) -> Optional[str]:
        """Get file path for a resource ID"""
        return self.file_map.get(resource_id)

    def get_course_structure(self) -> Dict[str, any]:
        """
        Get hierarchical course structure
        
        Returns:
            Dictionary representing course organization
        """
        return {
            "resources": self.resource_map,
            "file_map": self.file_map,
            "organizations": self.organization_map,
        }


def parse_blackboard_export(zip_path: Path) -> Dict[str, any]:
    """
    Convenience function to parse a Blackboard export
    
    Args:
        zip_path: Path to Blackboard export ZIP
        
    Returns:
        Parsed manifest data
    """
    parser = BlackboardParser(zip_path)
    return parser.parse_manifest()

