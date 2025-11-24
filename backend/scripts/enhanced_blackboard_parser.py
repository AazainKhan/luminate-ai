#!/usr/bin/env python3
"""
Enhanced Blackboard Parser
Parses ALL .dat files to build complete course structure and resource mappings
"""

import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedBlackboardParser:
    """Comprehensive parser for Blackboard export files"""
    
    def __init__(self, export_dir: Path):
        self.export_dir = export_dir
        self.manifest_path = export_dir / "imsmanifest.xml"
        
        # Resource mappings
        self.resource_to_title = {}  # resource_id -> title
        self.resource_to_parent = {}  # resource_id -> parent_id
        self.parent_to_children = defaultdict(list)  # parent_id -> [child_ids]
        self.content_to_module = {}  # content_id -> module info
        self.resource_links = {}  # resource_id -> file info
        self.item_hierarchy = {}  # item_id -> {title, parent, level}
        
        # File mappings
        self.xid_to_file = {}  # __xid-XXX_1 -> actual file path
        self.file_to_context = {}  # file_path -> course context
        
    def parse_all(self):
        """Parse all data sources"""
        logger.info("="*80)
        logger.info("ENHANCED BLACKBOARD PARSER - COMPREHENSIVE ANALYSIS")
        logger.info("="*80)
        
        # Step 1: Parse manifest for top-level structure
        self.parse_manifest()
        
        # Step 2: Parse all .dat files for resource links
        self.parse_dat_files()
        
        # Step 3: Build complete hierarchy
        self.build_hierarchy()
        
        # Step 4: Map files to context
        self.map_files_to_context()
        
        logger.info("\n" + "="*80)
        logger.info("PARSING COMPLETE")
        logger.info("="*80)
        logger.info(f"Resources mapped: {len(self.resource_to_title)}")
        logger.info(f"Content items: {len(self.content_to_module)}")
        logger.info(f"Files mapped: {len(self.file_to_context)}")
        
    def parse_manifest(self):
        """Parse imsmanifest.xml for course structure"""
        if not self.manifest_path.exists():
            logger.warning("imsmanifest.xml not found")
            return
        
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            # Parse organization structure
            for item in root.findall('.//{*}item'):
                item_id = item.get('identifier')
                identifierref = item.get('identifierref')
                
                # Get title
                title_elem = item.find('{*}title')
                title = title_elem.text if title_elem is not None else 'Unknown'
                
                # Find parent
                parent = None
                for potential_parent in root.findall('.//{*}item'):
                    for child in potential_parent.findall('{*}item'):
                        if child.get('identifier') == item_id:
                            parent = potential_parent.get('identifier')
                            break
                
                self.item_hierarchy[item_id] = {
                    'title': title,
                    'parent': parent,
                    'identifierref': identifierref
                }
                
                if identifierref:
                    self.resource_to_title[identifierref] = title
                    if parent:
                        self.resource_to_parent[identifierref] = parent
            
            # Parse resources
            for resource in root.findall('.//{*}resource'):
                res_id = resource.get('identifier')
                href = resource.get('href')
                
                if res_id and href:
                    self.resource_links[res_id] = {
                        'href': href,
                        'type': resource.get('type', 'unknown')
                    }
            
            logger.info(f"✅ Parsed manifest: {len(self.item_hierarchy)} items, {len(self.resource_links)} resources")
        except Exception as e:
            logger.error(f"❌ Error parsing manifest: {e}")
    
    def parse_dat_files(self):
        """Parse all .dat files for resource links and metadata"""
        dat_files = list(self.export_dir.rglob("*.dat"))
        logger.info(f"\n📄 Parsing {len(dat_files)} .dat files...")
        
        parsed_count = 0
        for dat_file in dat_files:
            try:
                with open(dat_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Try to parse as XML
                if content.strip().startswith('<?xml'):
                    self._parse_xml_dat(dat_file, content)
                    parsed_count += 1
                
            except Exception as e:
                logger.debug(f"Could not parse {dat_file.name}: {e}")
        
        logger.info(f"✅ Parsed {parsed_count} XML .dat files")
    
    def _parse_xml_dat(self, dat_file: Path, content: str):
        """Parse XML content from .dat file"""
        try:
            root = ET.fromstring(content)
            
            # Parse resource links
            for link in root.findall('.//cms_resource_link'):
                resource_id_elem = link.find('resourceId')
                parent_id_elem = link.find('parentId')
                
                if resource_id_elem is not None and parent_id_elem is not None:
                    resource_id = resource_id_elem.text
                    parent_id = parent_id_elem.text
                    parent_type = parent_id_elem.get('parent_data_type', 'unknown')
                    
                    if resource_id and parent_id:
                        self.resource_to_parent[resource_id] = parent_id
                        self.parent_to_children[parent_id].append(resource_id)
            
            # Parse content items
            for content_elem in root.findall('.//content'):
                content_id = content_elem.get('id')
                title_elem = content_elem.find('title')
                
                if content_id and title_elem is not None:
                    title = title_elem.get('value', '')
                    self.resource_to_title[content_id] = title
            
            # Parse messages (announcements, etc.)
            for msg in root.findall('.//message'):
                msg_id = msg.get('id')
                title_elem = msg.find('title')
                
                if msg_id and title_elem is not None:
                    title = title_elem.get('value', '')
                    self.resource_to_title[msg_id] = title
            
        except ET.ParseError:
            pass  # Not valid XML, skip
    
    def build_hierarchy(self):
        """Build complete content hierarchy with module/week information"""
        logger.info("\n🔗 Building content hierarchy...")
        
        # Extract module information from titles
        for item_id, item_info in self.item_hierarchy.items():
            title = item_info['title']
            
            # Extract module number
            module_num = None
            week_num = None
            
            if 'Module' in title or 'module' in title:
                # Try to extract module number
                import re
                match = re.search(r'Module\s+(\d+)', title, re.IGNORECASE)
                if match:
                    module_num = int(match.group(1))
                    week_num = module_num
            
            # Find all descendants
            self._propagate_module_info(item_id, module_num, week_num, title)
        
        logger.info(f"✅ Built hierarchy: {len(self.content_to_module)} content items mapped")
    
    def _propagate_module_info(self, item_id: str, module_num: Optional[int], 
                                week_num: Optional[int], parent_title: str):
        """Recursively propagate module info to children"""
        item_info = self.item_hierarchy.get(item_id)
        if not item_info:
            return
        
        current_title = item_info['title']
        
        # Try to extract module from current title if not already set
        if not module_num:
            import re
            # Check for "Topic 6.4" or "Module 6" patterns
            match_topic = re.search(r'Topic\s+(\d+)\.', current_title, re.IGNORECASE)
            match_module = re.search(r'Module\s+(\d+)', current_title, re.IGNORECASE)
            
            if match_topic:
                module_num = int(match_topic.group(1))
                week_num = module_num
            elif match_module:
                module_num = int(match_module.group(1))
                week_num = module_num
        
        identifierref = item_info.get('identifierref')
        if identifierref:
            self.content_to_module[identifierref] = {
                'module': f"Module {module_num}" if module_num else "Unknown",
                'week': week_num,
                'parent_title': parent_title,
                'title': current_title
            }
        
        # Propagate to children
        for child_id, child_info in self.item_hierarchy.items():
            if child_info.get('parent') == item_id:
                self._propagate_module_info(child_id, module_num, week_num, current_title)
    
    def map_files_to_context(self):
        """Map actual files to course context"""
        logger.info("\n📁 Mapping files to course context...")
        
        # Map all media files
        for file_path in self.export_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip .dat files themselves
            if file_path.suffix == '.dat':
                continue
            
            rel_path = str(file_path.relative_to(self.export_dir))
            
            # Try to find context
            context = self._find_file_context(file_path, rel_path)
            if context:
                self.file_to_context[str(file_path)] = context
        
        logger.info(f"✅ Mapped {len(self.file_to_context)} files to context")
    
    def _find_file_context(self, file_path: Path, rel_path: str) -> Optional[Dict]:
        """Find course context for a file"""
        # Strategy 1: Check if file is in a resource directory (resXXXXX)
        parts = rel_path.split('/')
        for part in parts:
            if part.startswith('res') and part[3:].split('.')[0].isdigit():
                res_id = part.split('.')[0]
                if res_id in self.content_to_module:
                    return self.content_to_module[res_id]
                if res_id in self.resource_to_title:
                    return {
                        'module': 'Unknown',
                        'week': None,
                        'parent_title': 'Unknown',
                        'title': self.resource_to_title[res_id]
                    }
        
        # Strategy 2: Check if filename contains resource ID (__xid-XXXXX_1)
        import re
        xid_match = re.search(r'__xid-(\d+)_(\d+)', str(file_path))
        if xid_match:
            resource_id = f"{xid_match.group(1)}_{xid_match.group(2)}"
            
            # Look for parent in resource mappings
            if resource_id in self.resource_to_parent:
                parent_id = self.resource_to_parent[resource_id]
                if parent_id in self.resource_to_title:
                    return {
                        'module': 'Unknown',
                        'week': None,
                        'parent_title': self.resource_to_title.get(parent_id, 'Unknown'),
                        'title': self.resource_to_title.get(resource_id, file_path.name)
                    }
        
        # Strategy 3: Check csfiles directory structure
        if 'csfiles/home_dir' in rel_path:
            # These are user-uploaded files, try to find parent folder context
            parent_dir = file_path.parent.name
            if parent_dir.startswith('__xid-'):
                xid = parent_dir.replace('__xid-', '').replace('_', '_')
                if xid in self.resource_to_title:
                    return {
                        'module': 'Unknown',
                        'week': None,
                        'parent_title': self.resource_to_title[xid],
                        'title': file_path.name
                    }
        
        return None
    
    def get_file_context(self, file_path: str) -> Dict:
        """Get context for a specific file"""
        abs_path = str(Path(file_path).resolve())
        
        if abs_path in self.file_to_context:
            return self.file_to_context[abs_path]
        
        # Try relative path
        for mapped_path, context in self.file_to_context.items():
            if file_path in mapped_path:
                return context
        
        return {
            'module': 'Unknown',
            'week': None,
            'parent_title': 'Unknown',
            'title': Path(file_path).name
        }
    
    def export_mappings(self, output_path: Path):
        """Export all mappings to JSON"""
        mappings = {
            'resource_to_title': self.resource_to_title,
            'content_to_module': self.content_to_module,
            'file_to_context': {k: v for k, v in self.file_to_context.items()},
            'statistics': {
                'total_resources': len(self.resource_to_title),
                'total_content_items': len(self.content_to_module),
                'total_files_mapped': len(self.file_to_context),
                'total_items_in_hierarchy': len(self.item_hierarchy)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Exported mappings to: {output_path}")


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent
    export_dir = project_root / "raw_data" / "ExportFile_COMP237"
    output_dir = project_root / "backend" / "cleaned_data"
    
    if not export_dir.exists():
        logger.error(f"❌ Export directory not found: {export_dir}")
        return 1
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse everything
    parser = EnhancedBlackboardParser(export_dir)
    parser.parse_all()
    
    # Export mappings
    mappings_path = output_dir / "blackboard_mappings.json"
    parser.export_mappings(mappings_path)
    
    logger.info("\n" + "="*80)
    logger.info("✅ ENHANCED PARSING COMPLETE")
    logger.info("="*80)
    logger.info(f"\nNext step: Run generate_media_inventory.py to regenerate with accurate context")
    
    return 0


if __name__ == "__main__":
    exit(main())

