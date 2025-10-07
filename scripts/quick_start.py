#!/usr/bin/env python3
"""
Quick Start Example for Luminate AI Ingestion Pipeline
=======================================================

This script demonstrates how to use the ingestion pipeline and work with the output.
"""

import json
from pathlib import Path
from ingest_clean_luminate import Config, IngestionPipeline


def run_basic_ingestion():
    """Run the basic ingestion pipeline."""
    print("=" * 80)
    print("LUMINATE AI - QUICK START EXAMPLE")
    print("=" * 80)
    
    # 1. Create configuration
    print("\n1. Setting up configuration...")
    config = Config(
        source_dir=Path('extracted/ExportFile_COMP237_INP'),
        output_dir=Path('cleaned'),
        course_id='_29430_1',
        course_name='Luminate'
    )
    
    # 2. Run pipeline
    print("2. Running ingestion pipeline...")
    pipeline = IngestionPipeline(config)
    pipeline.run()
    
    print("\n✅ Ingestion complete!")


def explore_output():
    """Explore and analyze the generated output."""
    print("\n" + "=" * 80)
    print("EXPLORING OUTPUT")
    print("=" * 80)
    
    # 1. Load summary
    print("\n1. Loading summary...")
    with open('ingest_summary.json', 'r') as f:
        summary = json.load(f)
    
    print(f"   Total files processed: {summary['statistics']['processed_files']}")
    print(f"   Total chunks created: {summary['statistics']['total_chunks']}")
    print(f"   Total tokens: {summary['statistics']['total_tokens']:,}")
    
    # 2. Show module breakdown
    print("\n2. Module breakdown:")
    for module, stats in summary['by_module'].items():
        print(f"   {module}:")
        print(f"     Files: {stats['files']}")
        print(f"     Chunks: {stats['chunks']}")
        print(f"     Tokens: {stats['tokens']:,}")
    
    # 3. Load and inspect a sample document
    print("\n3. Sample document:")
    cleaned_dir = Path('cleaned')
    json_files = list(cleaned_dir.rglob('*.json'))
    
    if json_files:
        sample_file = json_files[0]
        with open(sample_file, 'r') as f:
            doc = json.load(f)
        
        print(f"   File: {doc['file_name']}")
        print(f"   Module: {doc['module']}")
        print(f"   BB Doc ID: {doc['bb_doc_id']}")
        print(f"   Live URL: {doc['live_lms_url']}")
        print(f"   Number of chunks: {doc['num_chunks']}")
        
        if doc['chunks']:
            chunk = doc['chunks'][0]
            print(f"\n   First chunk preview:")
            print(f"   ID: {chunk['chunk_id']}")
            print(f"   Content (first 200 chars):")
            print(f"   {chunk['content'][:200]}...")
    
    # 4. Load and inspect graph
    print("\n4. Graph relationships:")
    graph_file = Path('graph_seed/graph_links.json')
    if graph_file.exists():
        with open(graph_file, 'r') as f:
            links = json.load(f)
        
        print(f"   Total relationships: {len(links)}")
        
        # Count by relation type
        relation_counts = {}
        for link in links:
            rel = link['relation']
            relation_counts[rel] = relation_counts.get(rel, 0) + 1
        
        for relation, count in relation_counts.items():
            print(f"   {relation}: {count}")
        
        # Show sample links
        print(f"\n   Sample relationships:")
        for link in links[:3]:
            print(f"   {link['source']} --[{link['relation']}]--> {link['target']}")


def load_chunks_for_chromadb():
    """Example: Load chunks ready for ChromaDB ingestion."""
    print("\n" + "=" * 80)
    print("PREPARING FOR CHROMADB")
    print("=" * 80)
    
    all_chunks = []
    cleaned_dir = Path('cleaned')
    
    print("\nCollecting chunks from all documents...")
    for json_file in cleaned_dir.rglob('*.json'):
        with open(json_file, 'r') as f:
            doc = json.load(f)
        
        for chunk in doc['chunks']:
            # Add document-level metadata to each chunk
            chunk_with_metadata = {
                'id': chunk['chunk_id'],
                'content': chunk['content'],
                'metadata': {
                    'course_id': doc['course_id'],
                    'course_name': doc['course_name'],
                    'module': doc['module'],
                    'file_name': doc['file_name'],
                    'bb_doc_id': doc['bb_doc_id'],
                    'live_lms_url': chunk['live_lms_url'],
                    'tags': chunk['tags'],
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks']
                }
            }
            all_chunks.append(chunk_with_metadata)
    
    print(f"✅ Collected {len(all_chunks)} chunks ready for ChromaDB")
    
    # Save to a single file for easy loading
    output_file = Path('chromadb_ready.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}")
    
    # Show example of how to use with ChromaDB
    print("\n" + "Example ChromaDB usage:")
    print("-" * 80)
    print("""
import chromadb
import json

# Load chunks
with open('chromadb_ready.json', 'r') as f:
    chunks = json.load(f)

# Initialize ChromaDB
client = chromadb.Client()
collection = client.create_collection(
    name="luminate_course",
    metadata={"description": "Luminate AI course content"}
)

# Add chunks in batches
batch_size = 100
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    
    collection.add(
        ids=[c['id'] for c in batch],
        documents=[c['content'] for c in batch],
        metadatas=[c['metadata'] for c in batch]
    )

print(f"✅ Added {len(chunks)} chunks to ChromaDB")

# Query example
results = collection.query(
    query_texts=["What is artificial intelligence?"],
    n_results=5
)

for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"\\nResult {i+1}:")
    print(f"Module: {metadata['module']}")
    print(f"Live URL: {metadata['live_lms_url']}")
    print(f"Content: {doc[:200]}...")
    """)
    print("-" * 80)


def analyze_issues():
    """Analyze any issues that occurred during ingestion."""
    print("\n" + "=" * 80)
    print("ISSUE ANALYSIS")
    print("=" * 80)
    
    issues_file = Path('logs/ingest_issues.txt')
    
    if issues_file.exists():
        with open(issues_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        issues = [l for l in lines if l.strip() and not l.startswith('=') and 'Generated:' not in l]
        
        if issues:
            print(f"\n⚠️  Found {len(issues)} issues:")
            
            # Categorize issues
            errors = [i for i in issues if '[ERROR]' in i]
            warnings = [i for i in issues if '[WARNING]' in i]
            skips = [i for i in issues if '[SKIP]' in i]
            
            print(f"   Errors: {len(errors)}")
            print(f"   Warnings: {len(warnings)}")
            print(f"   Skipped: {len(skips)}")
            
            if errors:
                print(f"\n   Recent errors:")
                for error in errors[:5]:
                    print(f"   {error}")
        else:
            print("\n✅ No issues found!")
    else:
        print("\n✅ No issues file found (perfect run!)")


def main():
    """Run the quick start examples."""
    import sys
    
    print("\nLUMINATE AI - QUICK START EXAMPLES")
    print("=" * 80)
    print("\nSelect an option:")
    print("1. Run full ingestion pipeline")
    print("2. Explore existing output")
    print("3. Prepare chunks for ChromaDB")
    print("4. Analyze issues")
    print("5. Run all examples")
    print("\nEnter choice (1-5): ", end='')
    
    try:
        choice = input().strip()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    
    if choice == '1':
        run_basic_ingestion()
    elif choice == '2':
        explore_output()
    elif choice == '3':
        load_chunks_for_chromadb()
    elif choice == '4':
        analyze_issues()
    elif choice == '5':
        run_basic_ingestion()
        explore_output()
        load_chunks_for_chromadb()
        analyze_issues()
    else:
        print("Invalid choice. Running all examples...")
        run_basic_ingestion()
        explore_output()
        load_chunks_for_chromadb()
        analyze_issues()
    
    print("\n" + "=" * 80)
    print("QUICK START COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the output in the 'cleaned/' directory")
    print("2. Check 'ingest_summary.json' for statistics")
    print("3. Examine 'graph_seed/graph_links.json' for relationships")
    print("4. Use 'chromadb_ready.json' for embedding/indexing")
    print("5. Check 'logs/' for detailed logs and issues")
    print("\nFor more information, see README.md")
    print("=" * 80)


if __name__ == '__main__':
    main()
