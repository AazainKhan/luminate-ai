#!/usr/bin/env python3
"""
Clean ChromaDB - Remove System Files

Removes entries from ChromaDB that have module="csfiles" or other system/navigation metadata.
These are Blackboard internal files that shouldn't appear in search results.

Usage:
    python3 scripts/clean_chromadb_csfiles.py

This will:
1. Connect to ChromaDB at ./chromadb_data
2. Query for all documents with module="csfiles"
3. Delete those documents
4. Report statistics
"""

import chromadb
from typing import List, Dict, Any


SYSTEM_MODULES_TO_REMOVE = [
    "csfiles",
    "system",
    "navigation",
    "__internals",
    "__system",
]


def clean_chromadb():
    """Remove system files from ChromaDB collection"""
    
    print("=" * 60)
    print("ChromaDB Cleanup - Removing System Files")
    print("=" * 60)
    
    # Connect to ChromaDB
    print("\n1. Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./chromadb_data")
    collection = client.get_collection(name="comp237_content")
    
    initial_count = collection.count()
    print(f"   Initial document count: {initial_count}")
    
    # Get all documents to check their modules
    print("\n2. Scanning for system files...")
    all_docs = collection.get(include=["metadatas"])
    
    # Find IDs of documents to delete
    ids_to_delete = []
    modules_found = {}
    
    for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
        module = metadata.get("module", "").lower()
        
        # Track module distribution
        modules_found[module] = modules_found.get(module, 0) + 1
        
        # Check if this is a system module
        if module in SYSTEM_MODULES_TO_REMOVE:
            ids_to_delete.append(doc_id)
    
    print(f"\n   Module distribution:")
    for module, count in sorted(modules_found.items(), key=lambda x: -x[1]):
        marker = " ❌ [TO DELETE]" if module in SYSTEM_MODULES_TO_REMOVE else ""
        print(f"   - {module}: {count} documents{marker}")
    
    # Delete system files
    if ids_to_delete:
        print(f"\n3. Deleting {len(ids_to_delete)} system file entries...")
        
        # ChromaDB delete in batches (max 1000 per batch)
        batch_size = 1000
        for i in range(0, len(ids_to_delete), batch_size):
            batch = ids_to_delete[i:i+batch_size]
            collection.delete(ids=batch)
            print(f"   Deleted batch {i//batch_size + 1}: {len(batch)} documents")
        
        final_count = collection.count()
        print(f"\n   Final document count: {final_count}")
        print(f"   ✅ Removed: {initial_count - final_count} documents")
    else:
        print("\n   ✅ No system files found - database is clean!")
    
    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)


def verify_cleanup():
    """Verify no csfiles remain in the collection"""
    
    print("\n4. Verifying cleanup...")
    
    client = chromadb.PersistentClient(path="./chromadb_data")
    collection = client.get_collection(name="comp237_content")
    
    # Try to query for csfiles
    all_docs = collection.get(include=["metadatas"])
    
    csfiles_found = []
    for doc_id, metadata in zip(all_docs["ids"], all_docs["metadatas"]):
        module = metadata.get("module", "").lower()
        if module in SYSTEM_MODULES_TO_REMOVE:
            csfiles_found.append((doc_id, module))
    
    if csfiles_found:
        print(f"   ⚠️  WARNING: Still found {len(csfiles_found)} system files!")
        for doc_id, module in csfiles_found[:5]:
            print(f"      - {doc_id}: {module}")
    else:
        print("   ✅ Verification passed - no system files remain!")


if __name__ == "__main__":
    try:
        clean_chromadb()
        verify_cleanup()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
