"""
Load sample data from chroma_input.jsonl into ChromaDB
"""
import json
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

# Create or get collection
try:
    collection = client.get_collection("course_comp237")
    print(f"Collection 'course_comp237' already exists with {collection.count()} documents")
except:
    collection = client.create_collection("course_comp237")
    print("Created new collection 'course_comp237'")

# Load data from JSONL file
documents = []
metadatas = []
ids = []

print("Loading data from chroma_input.jsonl...")
with open('./data/chroma_input.jsonl', 'r') as f:
    for line_num, line in enumerate(f, 1):
        if line.strip():
            try:
                data = json.loads(line)
                documents.append(data['text'])
                metadatas.append({
                    'topic': data.get('topic', ''),
                    'subtopic': data.get('subtopic', ''),
                    'section_heading': data.get('section_heading', ''),
                    'source_title': data.get('source_title', ''),
                    'difficulty_level': data.get('difficulty_level', ''),
                    'content_type': data.get('content_type', ''),
                    'chunk_index': data.get('chunk_index', 0)
                })
                ids.append(data['id'])
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")

print(f"Loaded {len(documents)} documents")

# Add documents to collection in batches
batch_size = 100
for i in range(0, len(documents), batch_size):
    end_idx = min(i + batch_size, len(documents))
    collection.add(
        documents=documents[i:end_idx],
        metadatas=metadatas[i:end_idx],
        ids=ids[i:end_idx]
    )
    print(f"Added batch {i//batch_size + 1}: documents {i+1} to {end_idx}")

print(f"\nTotal documents in collection: {collection.count()}")

# Test query
print("\nTesting query for 'A* search'...")
results = collection.query(
    query_texts=["A* search algorithm"],
    n_results=3
)

print(f"Found {len(results['documents'][0])} results:")
for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
    print(f"\nResult {i+1} (distance: {dist:.4f}):")
    print(f"Preview: {doc[:200]}...")

print("\n✅ Data loaded successfully!")
