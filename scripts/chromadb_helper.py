#!/usr/bin/env python3
"""
ChromaDB Integration Helper for Luminate AI
============================================

This script helps you load the processed chunks into ChromaDB and test queries.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not installed. Install with: pip install chromadb")


class LuminateChromaDB:
    """Helper class for ChromaDB integration."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client."""
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = None
    
    def create_collection(self, name: str = "luminate_course", reset: bool = False):
        """Create or get a collection."""
        if reset:
            try:
                self.client.delete_collection(name)
                print(f"🗑️  Deleted existing collection: {name}")
            except:
                pass
        
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={
                "description": "Luminate AI course content with live LMS links",
                "source": "Blackboard LMS export"
            }
        )
        print(f"✅ Collection ready: {name}")
        return self.collection
    
    def load_chunks_from_json(self, json_path: str = "chromadb_ready.json"):
        """Load chunks from the prepared JSON file."""
        json_file = Path(json_path)
        
        if not json_file.exists():
            print(f"❌ File not found: {json_path}")
            print("   Run quick_start.py first to generate this file.")
            return 0
        
        print(f"📂 Loading chunks from {json_path}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"   Found {len(chunks)} chunks")
        
        if not self.collection:
            self.create_collection()
        
        # Add in batches
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            self.collection.add(
                ids=[c['id'] for c in batch],
                documents=[c['content'] for c in batch],
                metadatas=[c['metadata'] for c in batch]
            )
            
            total_added += len(batch)
            print(f"   Added {total_added}/{len(chunks)} chunks...", end='\r')
        
        print(f"\n✅ Successfully added {total_added} chunks to ChromaDB")
        return total_added
    
    def load_chunks_from_cleaned_dir(self, cleaned_dir: str = "cleaned"):
        """Load chunks directly from the cleaned directory."""
        cleaned_path = Path(cleaned_dir)
        
        if not cleaned_path.exists():
            print(f"❌ Directory not found: {cleaned_dir}")
            print("   Run ingest_clean_luminate.py first.")
            return 0
        
        print(f"📂 Loading chunks from {cleaned_dir}...")
        
        all_chunks = []
        json_files = list(cleaned_path.rglob('*.json'))
        
        print(f"   Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)
            
            for chunk in doc['chunks']:
                chunk_data = {
                    'id': chunk['chunk_id'],
                    'content': chunk['content'],
                    'metadata': {
                        'course_id': doc['course_id'],
                        'course_name': doc['course_name'],
                        'module': doc['module'],
                        'file_name': doc['file_name'],
                        'bb_doc_id': doc.get('bb_doc_id', ''),
                        'live_lms_url': chunk.get('live_lms_url', ''),
                        'tags': ','.join(chunk.get('tags', [])),
                        'chunk_index': chunk['chunk_index'],
                        'total_chunks': chunk['total_chunks']
                    }
                }
                all_chunks.append(chunk_data)
        
        print(f"   Collected {len(all_chunks)} chunks")
        
        if not self.collection:
            self.create_collection()
        
        # Add in batches
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            
            self.collection.add(
                ids=[c['id'] for c in batch],
                documents=[c['content'] for c in batch],
                metadatas=[c['metadata'] for c in batch]
            )
            
            total_added += len(batch)
            print(f"   Added {total_added}/{len(all_chunks)} chunks...", end='\r')
        
        print(f"\n✅ Successfully added {total_added} chunks to ChromaDB")
        return total_added
    
    def query(self, query_text: str, n_results: int = 5, 
              module_filter: Optional[str] = None) -> Dict:
        """Query the collection."""
        if not self.collection:
            print("❌ No collection loaded. Create one first.")
            return {}
        
        where_filter = None
        if module_filter:
            where_filter = {"module": module_filter}
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        
        return results
    
    def display_results(self, results: Dict, show_content: bool = True):
        """Display query results in a nice format."""
        if not results or not results.get('documents'):
            print("No results found.")
            return
        
        print("\n" + "=" * 80)
        print("QUERY RESULTS")
        print("=" * 80)
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0] if 'distances' in results else [0] * len(results['documents'][0])
        )):
            print(f"\n📄 Result {i+1}")
            print(f"   Score: {1 - distance:.4f}" if distance else "")
            print(f"   Module: {metadata.get('module', 'N/A')}")
            print(f"   File: {metadata.get('file_name', 'N/A')}")
            print(f"   Chunk: {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', 1)}")
            
            if metadata.get('live_lms_url'):
                print(f"   🔗 Live URL: {metadata['live_lms_url']}")
            
            if show_content:
                print(f"\n   Content:")
                content_preview = doc[:300] + "..." if len(doc) > 300 else doc
                for line in content_preview.split('\n'):
                    print(f"   {line}")
        
        print("\n" + "=" * 80)
    
    def get_collection_stats(self):
        """Get statistics about the collection."""
        if not self.collection:
            print("❌ No collection loaded.")
            return
        
        count = self.collection.count()
        
        print("\n" + "=" * 80)
        print("COLLECTION STATISTICS")
        print("=" * 80)
        print(f"Total chunks: {count}")
        
        # Get sample to analyze
        if count > 0:
            sample = self.collection.get(limit=min(1000, count))
            
            # Count by module
            modules = {}
            for metadata in sample['metadatas']:
                module = metadata.get('module', 'Unknown')
                modules[module] = modules.get(module, 0) + 1
            
            print(f"\nChunks by module (sample of {len(sample['metadatas'])}):")
            for module, count in sorted(modules.items()):
                print(f"  {module}: {count}")
        
        print("=" * 80)


def interactive_query_session(db: LuminateChromaDB):
    """Run an interactive query session."""
    print("\n" + "=" * 80)
    print("INTERACTIVE QUERY SESSION")
    print("=" * 80)
    print("Enter queries to search the course content.")
    print("Commands:")
    print("  - Type a question to search")
    print("  - 'stats' to show collection statistics")
    print("  - 'quit' or 'exit' to exit")
    print("=" * 80)
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if query.lower() == 'stats':
                db.get_collection_stats()
                continue
            
            # Parse number of results if specified
            n_results = 5
            if query.endswith(')') and '(' in query:
                try:
                    parts = query.rsplit('(', 1)
                    n_results = int(parts[1].rstrip(')'))
                    query = parts[0].strip()
                except:
                    pass
            
            results = db.query(query, n_results=n_results)
            db.display_results(results, show_content=True)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ChromaDB integration for Luminate AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load chunks and start interactive session
  python chromadb_helper.py --load --interactive
  
  # Load from specific directory
  python chromadb_helper.py --load --cleaned-dir cleaned
  
  # Query from command line
  python chromadb_helper.py --query "What is artificial intelligence?"
  
  # Reset and reload
  python chromadb_helper.py --load --reset
        """
    )
    
    parser.add_argument('--load', action='store_true',
                       help='Load chunks into ChromaDB')
    parser.add_argument('--cleaned-dir', type=str, default='cleaned',
                       help='Directory containing cleaned JSON files')
    parser.add_argument('--json-file', type=str, default='chromadb_ready.json',
                       help='Prepared JSON file with chunks')
    parser.add_argument('--reset', action='store_true',
                       help='Reset collection before loading')
    parser.add_argument('--query', type=str,
                       help='Run a single query')
    parser.add_argument('--interactive', action='store_true',
                       help='Start interactive query session')
    parser.add_argument('--n-results', type=int, default=5,
                       help='Number of results to return')
    parser.add_argument('--stats', action='store_true',
                       help='Show collection statistics')
    
    args = parser.parse_args()
    
    if not CHROMADB_AVAILABLE:
        print("❌ ChromaDB not installed.")
        print("   Install with: pip install chromadb")
        return 1
    
    # Initialize
    db = LuminateChromaDB()
    db.create_collection(reset=args.reset)
    
    # Load data
    if args.load:
        # Try JSON file first, fall back to cleaned dir
        json_path = Path(args.json_file)
        if json_path.exists():
            db.load_chunks_from_json(str(json_path))
        else:
            db.load_chunks_from_cleaned_dir(args.cleaned_dir)
    
    # Show stats
    if args.stats:
        db.get_collection_stats()
    
    # Run query
    if args.query:
        results = db.query(args.query, n_results=args.n_results)
        db.display_results(results)
    
    # Interactive mode
    if args.interactive:
        interactive_query_session(db)
    
    # If no action specified, show help
    if not any([args.load, args.query, args.interactive, args.stats]):
        parser.print_help()
        print("\n💡 Tip: Start with: python chromadb_helper.py --load --interactive")


if __name__ == '__main__':
    main()
