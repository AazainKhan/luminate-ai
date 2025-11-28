
"""
01_ingest_comp237.py — Ingest Blackboard export into Chroma
Usage:
  python 01_ingest_comp237.py --zip "/path/to/ExportFile_COMP237_...zip" \
                              --persist "./chroma_db"
Effect:
  Creates/updates Chroma collection: course_comp237
"""
from __future__ import annotations
import argparse, os, zipfile, io, xml.etree.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, List

# Add the data directory to the path so we can import ingest_core
sys.path.insert(0, str(Path(__file__).parent))

from ingest_core import connect_chroma, get_or_create_collection, chunk_text, hash_id, clean_html

def parse_manifest(zf: zipfile.ZipFile) -> Dict[str, str]:
    """Return a mapping from resource href (like 'ppg/res00001.dat') to a human title if present."""
    title_map = {}
    try:
        with zf.open("imsmanifest.xml") as f:
            tree = ET.parse(f)
        root = tree.getroot()
        # IMSCP may have namespaces; strip them
        def strip(tag): return tag.split('}',1)[-1]
        for item in root.iter():
            if strip(item.tag) == "resource":
                href = item.attrib.get("href", "")
                title = item.attrib.get("identifier", "")  # fallback
                # Try to find a title in metadata
                for child in item:
                    if strip(child.tag) == "file" and not href:
                        href = child.attrib.get("href","")
                if href:
                    title_map[href] = title or href
    except Exception:
        pass
    return title_map

def collect_texts_from_zip(zip_path: str) -> List[Dict]:
    data = []
    with zipfile.ZipFile(zip_path) as zf:
        title_map = parse_manifest(zf)
        for info in zf.infolist():
            if not info.filename.lower().endswith(".dat"):
                continue
            with zf.open(info.filename) as f:
                raw = f.read().decode("utf-8", errors="ignore")
            text = clean_html(raw)
            if not text.strip():
                continue
            title = title_map.get(info.filename, os.path.basename(info.filename))
            data.append({
                "id": info.filename,
                "title": title,
                "text": text,
                "url": f"bb://{info.filename}",
                "meta": {"source": "comp237_zip", "path": info.filename, "course_id":"comp237", "type": "slides_or_page"}
            })
    return data

def upsert_course(collection, docs: List[Dict]):
    ids = []
    documents = []
    metadatas = []
    for d in docs:
        chunks = chunk_text(d["text"])
        for idx, ch in enumerate(chunks):
            ids.append(hash_id("comp237", d["id"], str(idx)))
            documents.append(ch)
            md = (d.get("meta") or {}).copy()
            md.update({"title": d["title"], "url": d.get("url"), "ns": "course"})
            metadatas.append(md)
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="Path to Blackboard export zip (COMP237)")
    ap.add_argument("--persist", default="./chroma_db", help="ChromaDB persist directory")
    args = ap.parse_args()

    client, ef = connect_chroma(args.persist)
    col = get_or_create_collection(client, "course_comp237", ef)
    docs = collect_texts_from_zip(args.zip)
    upsert_course(col, docs)
    print(f"Ingested {len(docs)} files into course_comp237")

if __name__ == "__main__":
    main()
