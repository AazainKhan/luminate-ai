"""
Ingest COMP237 course content from Blackboard export into ChromaDB
"""
import os
import sys
import hashlib
import chromadb
from pathlib import Path
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config.chroma_config import CHROMA_SETTINGS

def clean_html(html_text):
    """Remove HTML tags and clean up text"""
    soup = BeautifulSoup(html_text, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    return text

def chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def hash_id(text):
    """Generate a unique ID for content"""
    return hashlib.md5(text.encode()).hexdigest()

def main():
    # Initialize ChromaDB
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db", settings=CHROMA_SETTINGS)
    
    # Delete existing collection and create new one
    try:
        client.delete_collection("course_comp237")
        print("Deleted existing course_comp237 collection")
    except:
        pass
    
    collection = client.create_collection("course_comp237")
    print("Created new course_comp237 collection")
    
    # Process all .dat files
    content_dir = Path("./data/ExportFile_COMP237_INP 2")
    dat_files = list(content_dir.glob("*.dat"))
    
    print(f"\nFound {len(dat_files)} .dat files to process")
    
    all_documents = []
    all_metadatas = []
    all_ids = []
    
    for idx, dat_file in enumerate(dat_files, 1):
        try:
            with open(dat_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Clean HTML if present
            if '<' in content and '>' in content:
                content = clean_html(content)
            
            # Skip if too short
            if len(content.strip()) < 50:
                continue
            
            # Chunk the content
            chunks = chunk_text(content, chunk_size=400, overlap=80)
            
            for chunk_idx, chunk in enumerate(chunks):
                doc_id = hash_id(f"{dat_file.name}_{chunk_idx}_{chunk[:50]}")
                all_documents.append(chunk)
                all_metadatas.append({
                    'source_file': dat_file.name,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    'course': 'COMP237'
                })
                all_ids.append(doc_id)
            
            if idx % 50 == 0:
                print(f"Processed {idx}/{len(dat_files)} files...")
                
        except Exception as e:
            print(f"Error processing {dat_file.name}: {e}")
            continue
    
    print(f"\nTotal chunks created: {len(all_documents)}")
    
    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, len(all_documents), batch_size):
        end_idx = min(i + batch_size, len(all_documents))
        collection.add(
            documents=all_documents[i:end_idx],
            metadatas=all_metadatas[i:end_idx],
            ids=all_ids[i:end_idx]
        )
        print(f"Added batch {i//batch_size + 1}: chunks {i+1} to {end_idx}")
    
    print(f"\n✅ Ingestion complete!")
    print(f"Total documents in collection: {collection.count()}")
    
    # Test query
    print("\n" + "="*60)
    print("Testing retrieval with sample queries...")
    print("="*60)
    
    test_queries = [
        "A* search algorithm",
        "artificial intelligence",
        "machine learning"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = collection.query(query_texts=[query], n_results=2)
        if results['documents'][0]:
            print(f"Found {len(results['documents'][0])} results")
            print(f"Top result preview: {results['documents'][0][0][:200]}...")
        else:
            print("No results found")

if __name__ == "__main__":
    main()
