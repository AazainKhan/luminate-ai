"""
Quick HTML Course Data Ingestion into ChromaDB
Loads HTML course modules directly into ChromaDB
"""

import chromadb
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import hashlib

# Configuration
SOURCE_DIR = Path(r"C:\Users\yajus\OneDrive - Centennial College\SEMESTER-6\AI Capstone (Mayy Habayeb)\Week-6Submit\html_course")
CHROMA_DIR = Path(r"C:\Users\yajus\OneDrive - Centennial College\SEMESTER-6\AI Capstone (Mayy Habayeb)\luminate-ai-aazain\luminate-ai-aazain\chromadb_data")

def extract_text_from_html(html_path):
    """Extract clean text from HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
    except Exception as e:
        print(f"Error reading {html_path}: {e}")
        return None

def get_module_name(file_path):
    """Extract module name from path."""
    # Get parent folder name (e.g., module_01_ai_intro)
    module_folder = file_path.parent.name
    if module_folder.startswith("module_"):
        return module_folder.replace("_", " ").title()
    return "General"

def ingest_html_courses():
    """Main ingestion function."""
    print("🚀 Starting HTML Course Ingestion into ChromaDB...")
    print(f"📁 Source: {SOURCE_DIR}")
    print(f"💾 ChromaDB: {CHROMA_DIR}")
    
    # Initialize ChromaDB
    print("\n📦 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Create collection (or get existing)
    try:
        collection = client.get_collection("course_materials")
        print("✅ Using existing collection 'course_materials'")
    except:
        collection = client.create_collection(
            name="course_materials",
            metadata={"description": "AI Course Materials from HTML modules"}
        )
        print("✅ Created new collection 'course_materials'")
    
    # Find all HTML files
    html_files = list(SOURCE_DIR.rglob("*.html"))
    print(f"\n📄 Found {len(html_files)} HTML files")
    
    # Process each file
    documents = []
    metadatas = []
    ids = []
    
    print("\n🔄 Processing HTML files...")
    for html_file in tqdm(html_files):
        # Extract text
        text = extract_text_from_html(html_file)
        if not text or len(text) < 100:  # Skip very short content
            continue
        
        # Get module info
        module_name = get_module_name(html_file)
        file_name = html_file.name
        
        # Create unique ID
        doc_id = hashlib.md5(str(html_file).encode()).hexdigest()[:16]
        
        # Prepare metadata
        metadata = {
            "title": file_name.replace(".html", "").replace("_", " "),
            "module": module_name,
            "file_path": str(html_file.relative_to(SOURCE_DIR)),
            "content_type": "html",
            "source": "course_html"
        }
        
        # Add to batch
        documents.append(text[:10000])  # Limit to 10k chars per doc
        metadatas.append(metadata)
        ids.append(doc_id)
    
    # Insert into ChromaDB in batches
    print(f"\n💾 Inserting {len(documents)} documents into ChromaDB...")
    batch_size = 100
    for i in tqdm(range(0, len(documents), batch_size)):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
    
    # Verify
    count = collection.count()
    print(f"\n✅ Successfully ingested {count} documents into ChromaDB!")
    print(f"📊 ChromaDB location: {CHROMA_DIR}")
    
    # Test query
    print("\n🧪 Testing retrieval with sample query...")
    results = collection.query(
        query_texts=["What is artificial intelligence?"],
        n_results=3
    )
    
    if results['documents'] and results['documents'][0]:
        print("\n✅ Retrieval test successful!")
        print(f"Sample result: {results['documents'][0][0][:200]}...")
    else:
        print("\n⚠️ Retrieval test returned no results")
    
    print("\n🎉 Ingestion complete!")
    return collection

if __name__ == "__main__":
    try:
        collection = ingest_html_courses()
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
