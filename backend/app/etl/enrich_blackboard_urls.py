"""
Blackboard URL Enrichment Script
Adds proper Blackboard Ultra URLs to course materials using content IDs
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Optional
import chromadb
from chromadb.config import Settings

# COMP237 Course ID - Extracted from Blackboard export res00001.dat
# Course: COMP237_INP.DEV - Introduction to AI (In Person) Development
# Verified: <COURSE id="_11378_1"> from ExportFile_COMP237/res00001.dat
COMP237_COURSE_ID = "_11378_1"

# Blackboard Ultra base URL
BLACKBOARD_BASE_URL = "https://luminate.centennialcollege.ca"


class BlackboardURLEnricher:
    """Enriches ChromaDB documents with Blackboard Ultra URLs"""
    
    def __init__(self, course_id: str = COMP237_COURSE_ID):
        """
        Initialize the enricher
        
        Args:
            course_id: Blackboard internal course ID (e.g., "_29430_1")
        """
        self.course_id = course_id
        self.content_id_map: Dict[str, Dict[str, str]] = {}
        
        # Connect to ChromaDB (use memory_store host inside Docker)
        import os
        chroma_host = os.getenv("CHROMADB_HOST", "memory_store")
        chroma_port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(anonymized_telemetry=False)
        )
    
    def load_content_ids(self, json_path: Path):
        """
        Load content ID mappings from blackboard_content_ids.json
        
        Args:
            json_path: Path to blackboard_content_ids.json file
        """
        print(f"Loading content ID mappings from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.content_id_map = json.load(f)
        
        print(f"✅ Loaded {len(self.content_id_map)} content ID mappings")
        
        # Show sample mappings
        sample = list(self.content_id_map.items())[:3]
        print("\n📋 Sample mappings:")
        for resource_id, ids in sample:
            print(f"  {resource_id}: content_id={ids['content_id']}, parent_id={ids['parent_id']}")
    
    def generate_blackboard_url(self, content_id: str, parent_id: Optional[str] = None) -> str:
        """
        Generate a Blackboard Ultra URL for a content item
        
        Args:
            content_id: Blackboard content ID (e.g., "_800667_1")
            parent_id: Parent content ID (optional)
        
        Returns:
            Full Blackboard Ultra URL
        
        Example:
            https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800667_1?courseId=_29430_1&view=content
        """
        # Blackboard Ultra URL structure:
        # /ultra/courses/{course_id}/outline/edit/document/{content_id}?courseId={course_id}&view=content
        
        url = (
            f"{BLACKBOARD_BASE_URL}/ultra/courses/{self.course_id}/"
            f"outline/edit/document/{content_id}"
            f"?courseId={self.course_id}&view=content"
        )
        
        return url
    
    def enrich_collection(self, collection_name: str = "comp237_course_materials"):
        """
        Enrich a ChromaDB collection with Blackboard URLs
        
        Args:
            collection_name: Name of the ChromaDB collection to enrich
        """
        print(f"\n🔄 Enriching collection: {collection_name}")
        
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"❌ Error: Collection '{collection_name}' not found: {e}")
            return
        
        # Get all documents
        results = collection.get(include=["metadatas", "documents"])
        total_docs = len(results['ids'])
        
        print(f"📊 Total documents in collection: {total_docs}")
        
        enriched_count = 0
        blackboard_urls_added = 0
        
        for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas'])):
            # Get resource_id from metadata
            resource_id = metadata.get('resource_id')
            
            if not resource_id:
                continue
            
            # Check if we have content ID mapping for this resource
            if resource_id not in self.content_id_map:
                continue
            
            content_info = self.content_id_map[resource_id]
            content_id = content_info.get('content_id')
            parent_id = content_info.get('parent_id')
            
            if not content_id:
                continue
            
            # Generate Blackboard URL
            blackboard_url = self.generate_blackboard_url(content_id, parent_id)
            
            # Parse existing URLs from metadata
            existing_urls = []
            try:
                if metadata.get('urls'):
                    parsed = json.loads(metadata['urls'])
                    # Handle both list of dicts and list of strings
                    if isinstance(parsed, list):
                        if parsed and isinstance(parsed[0], dict):
                            existing_urls = parsed
                        elif parsed and isinstance(parsed[0], str):
                            # Convert string URLs to dict format
                            existing_urls = [{"url": url, "type": "external"} for url in parsed]
            except:
                pass
            
            # Add Blackboard URL to the list
            blackboard_link = {
                "url": blackboard_url,
                "type": "blackboard"
            }
            
            # Check if Blackboard URL already exists
            has_blackboard = any(
                (isinstance(link, dict) and link.get('type') == 'blackboard') or
                (isinstance(link, str) and 'blackboard' in link)
                for link in existing_urls
            )
            
            if not has_blackboard:
                existing_urls.insert(0, blackboard_link)  # Add at the beginning (highest priority)
                blackboard_urls_added += 1
            
            # Parse existing URL types
            url_types = []
            try:
                if metadata.get('url_types'):
                    url_types = json.loads(metadata['url_types'])
            except:
                pass
            
            if not has_blackboard:
                url_types.insert(0, "blackboard")
            
            # Update primary URL to Blackboard (highest priority)
            new_metadata = metadata.copy()
            new_metadata['blackboard_url'] = blackboard_url
            new_metadata['blackboard_content_id'] = content_id
            new_metadata['blackboard_parent_id'] = parent_id
            new_metadata['urls'] = json.dumps(existing_urls)
            new_metadata['url_types'] = json.dumps(url_types)
            new_metadata['primary_url'] = blackboard_url  # Blackboard is now primary
            new_metadata['primary_url_type'] = "blackboard"
            new_metadata['has_urls'] = True
            
            # Update document in ChromaDB
            collection.update(
                ids=[doc_id],
                metadatas=[new_metadata]
            )
            
            enriched_count += 1
            
            # Show progress
            if (i + 1) % 50 == 0 or (i + 1) == total_docs:
                print(f"  Progress: {i + 1}/{total_docs} documents processed...")
        
        print(f"\n✅ Enrichment complete!")
        print(f"  - Documents enriched with Blackboard URLs: {enriched_count}")
        print(f"  - New Blackboard URLs added: {blackboard_urls_added}")
        
        return enriched_count, blackboard_urls_added
    
    def get_statistics(self, collection_name: str = "comp237_course_materials"):
        """
        Get statistics about Blackboard URLs in the collection
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        print(f"\n📊 Statistics for collection: {collection_name}")
        
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"❌ Error: Collection not found: {e}")
            return
        
        results = collection.get(include=["metadatas"])
        total_docs = len(results['ids'])
        
        blackboard_count = 0
        primary_blackboard_count = 0
        
        for metadata in results['metadatas']:
            if metadata.get('blackboard_url'):
                blackboard_count += 1
            if metadata.get('primary_url_type') == 'blackboard':
                primary_blackboard_count += 1
        
        print(f"  Total documents: {total_docs}")
        print(f"  Documents with Blackboard URLs: {blackboard_count} ({blackboard_count/total_docs*100:.1f}%)")
        print(f"  Documents with Blackboard as primary: {primary_blackboard_count} ({primary_blackboard_count/total_docs*100:.1f}%)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enrich ChromaDB with Blackboard Ultra URLs")
    parser.add_argument(
        "--content-ids-path",
        type=Path,
        default=Path("/app/data/processed/blackboard_content_ids.json"),
        help="Path to blackboard_content_ids.json file"
    )
    parser.add_argument(
        "--course-id",
        type=str,
        default=COMP237_COURSE_ID,
        help="Blackboard internal course ID (e.g., '_29430_1')"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="comp237_course_materials",
        help="ChromaDB collection name to enrich"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't enrich"
    )
    
    args = parser.parse_args()
    
    # Validate course ID - check if it's still the placeholder
    if args.course_id == "_REPLACE_WITH_ACTUAL_COURSE_ID_" and not args.stats_only:
        print("⚠️  WARNING: Course ID not configured!")
        print("   The COMP237_COURSE_ID is still set to placeholder value.")
        print("   Please update COMP237_COURSE_ID in the script or use --course-id flag")
        print("   Example: --course-id '_11378_1'")
        print()
        print("   To find your course ID:")
        print("   1. Go to COMP237 in Blackboard")
        print("   2. Click on any content item")
        print("   3. Look at the URL: https://luminate.centennialcollege.ca/ultra/courses/_XXXXX_1/...")
        print("   4. Copy the '_XXXXX_1' part")
        return
    
    print(f"✅ Using course ID: {args.course_id}")
    
    # Create enricher
    enricher = BlackboardURLEnricher(course_id=args.course_id)
    
    if args.stats_only:
        # Show statistics only
        enricher.get_statistics(args.collection)
    else:
        # Load content IDs and enrich
        enricher.load_content_ids(args.content_ids_path)
        enricher.enrich_collection(args.collection)
        enricher.get_statistics(args.collection)


if __name__ == "__main__":
    main()
