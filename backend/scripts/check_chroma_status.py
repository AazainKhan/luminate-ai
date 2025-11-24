
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chromadb_client import get_chromadb_client
import logging

logging.basicConfig(level=logging.INFO)

def main():
    try:
        client = get_chromadb_client()
        info = client.get_collection_info()
        print(f"Collection Info: {info}")
        
        # Peek to see data
        peek = client.collection.peek(limit=1)
        if peek and peek['metadatas']:
            print(f"Sample Metadata: {peek['metadatas'][0]}")
    except Exception as e:
        print(f"Error checking collection: {e}")

if __name__ == "__main__":
    main()
