"""
Enrich ChromaDB course materials with URLs from cleaned_content.json

This script adds URLs to existing ChromaDB documents by:
1. Loading cleaned_content.json (which contains links)
2. Querying ChromaDB for documents by resource_id
3. Updating metadata with URLs and link types
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class URLEnricher:
    """Enrich ChromaDB documents with URLs from cleaned_content.json"""
    
    def __init__(self, chromadb_host: str = "memory_store", chromadb_port: int = 8000):
        """Initialize URL enricher"""
        self.client = chromadb.HttpClient(
            host=chromadb_host,
            port=chromadb_port,
            settings=Settings(anonymized_telemetry=False)
        )
        self.url_map: Dict[str, List[Dict]] = {}  # resource_id -> links
        
    def load_cleaned_content(self, json_path: Path):
        """
        Load cleaned_content.json and extract URL mappings
        
        Args:
            json_path: Path to cleaned_content.json
        """
        logger.info(f"Loading cleaned content from {json_path}")
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Build resource_id -> links mapping
        for item in data:
            resource_id = item.get('resource_id')
            links = item.get('links', [])
            
            if resource_id and links:
                if resource_id not in self.url_map:
                    self.url_map[resource_id] = []
                self.url_map[resource_id].extend(links)
        
        # Deduplicate URLs per resource_id
        for resource_id in self.url_map:
            seen = set()
            unique_links = []
            for link in self.url_map[resource_id]:
                url = link.get('url', '')
                if url and url not in seen:
                    seen.add(url)
                    unique_links.append(link)
            self.url_map[resource_id] = unique_links
        
        logger.info(f"Loaded URL mappings for {len(self.url_map)} resources")
        
        # Stats
        total_urls = sum(len(links) for links in self.url_map.values())
        url_types = {}
        for links in self.url_map.values():
            for link in links:
                link_type = link.get('type', 'unknown')
                url_types[link_type] = url_types.get(link_type, 0) + 1
        
        logger.info(f"Total URLs: {total_urls}")
        logger.info(f"URL types: {url_types}")
        
    def enrich_collection(self, collection_name: str = "comp237_course_materials"):
        """
        Enrich ChromaDB collection with URLs
        
        Args:
            collection_name: Name of the collection to enrich
        """
        logger.info(f"Enriching collection: {collection_name}")
        
        try:
            collection = self.client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {e}")
            return
        
        # Get all documents from collection
        logger.info("Fetching all documents from collection...")
        all_docs = collection.get(include=['metadatas'])
        
        if not all_docs or not all_docs.get('ids'):
            logger.warning("No documents found in collection")
            return
        
        ids = all_docs['ids']
        metadatas = all_docs['metadatas']
        
        logger.info(f"Found {len(ids)} documents to potentially enrich")
        
        # Update metadata with URLs
        updated_count = 0
        for doc_id, metadata in zip(ids, metadatas):
            resource_id = metadata.get('resource_id')
            
            if not resource_id or resource_id not in self.url_map:
                continue
            
            links = self.url_map[resource_id]
            if not links:
                continue
            
            # Prepare URL metadata
            urls = [link['url'] for link in links]
            url_types = [link['type'] for link in links]
            
            # Find primary URL (prefer blackboard > mediasite > wikipedia > external > internal)
            # Note: Blackboard URLs are added separately via enrich_blackboard_urls.py
            priority = {'blackboard': 0, 'mediasite_video': 1, 'wikipedia': 2, 'external': 3, 'internal': 4}
            sorted_links = sorted(links, key=lambda x: priority.get(x['type'], 999))
            primary_url = sorted_links[0]['url'] if sorted_links else urls[0]
            primary_type = sorted_links[0]['type'] if sorted_links else url_types[0]
            
            # Update metadata
            new_metadata = metadata.copy()
            new_metadata['urls'] = json.dumps(urls)  # Store as JSON string
            new_metadata['url_types'] = json.dumps(url_types)
            new_metadata['primary_url'] = primary_url
            new_metadata['primary_url_type'] = primary_type
            new_metadata['has_urls'] = True
            
            # Update document in ChromaDB
            try:
                collection.update(
                    ids=[doc_id],
                    metadatas=[new_metadata]
                )
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} documents...")
                    
            except Exception as e:
                logger.error(f"Failed to update document {doc_id}: {e}")
        
        logger.info(f"✅ Enriched {updated_count} documents with URLs")
        
    def get_statistics(self, collection_name: str = "comp237_course_materials"):
        """Get statistics on URL enrichment"""
        try:
            collection = self.client.get_collection(collection_name)
            all_docs = collection.get(include=['metadatas'])
            
            if not all_docs or not all_docs.get('metadatas'):
                logger.warning("No documents found")
                return
            
            total_docs = len(all_docs['metadatas'])
            docs_with_urls = sum(1 for m in all_docs['metadatas'] if m.get('has_urls'))
            
            url_type_counts = {}
            for metadata in all_docs['metadatas']:
                if metadata.get('primary_url_type'):
                    url_type = metadata['primary_url_type']
                    url_type_counts[url_type] = url_type_counts.get(url_type, 0) + 1
            
            print(f"\n📊 URL Enrichment Statistics for {collection_name}")
            print(f"{'=' * 60}")
            print(f"Total documents: {total_docs}")
            print(f"Documents with URLs: {docs_with_urls} ({docs_with_urls/total_docs*100:.1f}%)")
            print(f"\nPrimary URL Types:")
            for url_type, count in sorted(url_type_counts.items(), key=lambda x: -x[1]):
                print(f"  {url_type}: {count}")
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")


def main():
    """Run URL enrichment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich ChromaDB with URLs")
    parser.add_argument(
        '--json-path',
        type=Path,
        default=Path('/app/data/processed/cleaned_content.json'),
        help='Path to cleaned_content.json'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='comp237_course_materials',
        help='ChromaDB collection name'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show statistics, do not update'
    )
    
    args = parser.parse_args()
    
    enricher = URLEnricher()
    
    if not args.stats_only:
        enricher.load_cleaned_content(args.json_path)
        enricher.enrich_collection(args.collection)
    
    enricher.get_statistics(args.collection)


if __name__ == '__main__':
    main()
