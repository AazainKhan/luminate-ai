
"""
02_ingest_oer.py — Ingest OER topics into Chroma from a JSONL file.
Each line can be either proper JSON like:
  {"topic":"Classical Search", "source":"MIT 6.034", "title":"A*", "text":"...", "url":"..."}
or a raw note block; raw blocks will be chunked with topic inferred from first line.
Usage:
  python 02_ingest_oer.py --jsonl /path/to/chroma_input.jsonl --persist ./chroma_db
Effect:
  Creates/updates Chroma collection: oer_resources
"""
from __future__ import annotations
import argparse, json, os
import sys
from pathlib import Path
from typing import List, Dict

# Add the data directory to the path so we can import ingest_core
sys.path.insert(0, str(Path(__file__).parent))

from ingest_core import connect_chroma, get_or_create_collection, chunk_text, hash_id

def parse_loose_jsonl(path: str) -> List[Dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        buf = ""
        for line in f:
            line = line.rstrip("\n")
            # Try strict JSON first
            try:
                obj = json.loads(line)
                docs.append(obj)
                continue
            except Exception:
                pass
            # Accumulate loose blocks (like pasted WhatsApp/notes)
            if line.strip() == "":
                if buf.strip():
                    first = buf.strip().splitlines()[0][:80]
                    docs.append({"topic": first, "source": "notes", "title": first, "text": buf.strip(), "url": None})
                    buf = ""
            else:
                buf += line + "\n"
        if buf.strip():
            first = buf.strip().splitlines()[0][:80]
            docs.append({"topic": first, "source": "notes", "title": first, "text": buf.strip(), "url": None})
    return docs

def upsert_oer(collection, docs: List[Dict]):
    ids=[]; documents=[]; metadatas=[]
    for d in docs:
        text = d.get("text","").strip()
        if not text: 
            continue
        chunks = chunk_text(text)
        for idx, ch in enumerate(chunks):
            # Create unique ID using original ID, topic, source_title and chunk index
            # This ensures uniqueness even when titles are empty or duplicate
            original_id = d.get("id", "")
            topic = d.get("topic", "")
            source_title = d.get("source_title", "")
            title = d.get("title", "")
            
            ids.append(hash_id("oer", original_id, topic, source_title, title, str(idx)))
            documents.append(ch)
            
            # Build metadata, filtering out None values
            metadata = {
                "ns": "oer",
                "type": "oer_note"
            }
            
            # Add non-None values
            if d.get("title") or d.get("topic"):
                metadata["title"] = d.get("title") or d.get("topic")
            if d.get("url") or d.get("source_url"):
                metadata["url"] = d.get("url") or d.get("source_url")
            if d.get("source") or d.get("source_title"):
                metadata["provider"] = d.get("source") or d.get("source_title")
            if d.get("id"):
                metadata["original_id"] = d.get("id")
            if d.get("topic"):
                metadata["topic"] = d.get("topic")
            if d.get("subtopic"):
                metadata["subtopic"] = d.get("subtopic")
            if d.get("section_heading"):
                metadata["section_heading"] = d.get("section_heading")
            if d.get("difficulty_level"):
                metadata["difficulty_level"] = d.get("difficulty_level")
            if d.get("content_type"):
                metadata["content_type"] = d.get("content_type")
                
            metadatas.append(metadata)
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="Path to chroma_input.jsonl (loose ok)")
    ap.add_argument("--persist", default="./chroma_db", help="ChromaDB persist directory")
    args = ap.parse_args()

    client, ef = connect_chroma(args.persist)
    col = get_or_create_collection(client, "oer_resources", ef)
    docs = parse_loose_jsonl(args.jsonl)
    upsert_oer(col, docs)
    print(f"Ingested {len(docs)} OER items into oer_resources")

if __name__ == "__main__":
    main()
