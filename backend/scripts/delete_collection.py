import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chromadb_client import get_chromadb_client
import logging

logging.basicConfig(level=logging.INFO)

def main():
    client = get_chromadb_client()
    try:
        client.delete_collection()
        print("✅ Collection deleted.")
    except Exception as e:
        print(f"❌ Error deleting collection: {e}")

if __name__ == "__main__":
    main()

