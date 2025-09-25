"""
embed_docs.py
- Reads chunks.jsonl
- Generates embeddings with sentence-transformers and stores them in ChromaDB.
Run locally where you have internet and python packages available:
pip install sentence-transformers chromadb
python embed_docs.py --chunks chunks.jsonl --persist_dir chroma_index
"""

import argparse, json, os
from sentence_transformers import SentenceTransformer
import chromadb

def main(chunks_path, persist_dir):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name="comp237_chunks")
    texts = []
    metadatas = []
    ids = []
    with open(chunks_path, "r", encoding="utf-8") as fr:
        for line in fr:
            obj = json.loads(line)
            texts.append(obj["text"])
            metadatas.append(obj["meta"])
            ids.append(obj["id"])
    embeddings = model.encode(texts, show_progress_bar=True)
    collection.add(ids=ids, embeddings=embeddings.tolist(), metadatas=metadatas, documents=texts)
    print(f"Stored {len(ids)} vectors in {persist_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", default="chunks.jsonl")
    parser.add_argument("--persist_dir", default="chroma_index")
    args = parser.parse_args()
    main(args.chunks, args.persist_dir)
