#!/usr/bin/env python3
"""
URL Verification Script
Validates that all generated URLs follow the correct Blackboard Ultra format.
"""

import json
from pathlib import Path
from collections import Counter
import re

def verify_url_format(url: str) -> tuple[bool, str]:
    """
    Verify URL follows Blackboard Ultra format.
    
    Expected format:
    https://luminate.centennialcollege.ca/ultra/courses/{COURSE_ID}/outline/edit/document/{DOC_ID}?courseId={COURSE_ID}&view=content&state=view
    """
    if not url:
        return False, "URL is None or empty"
    
    # Pattern for correct Blackboard Ultra URL
    pattern = r'^https://luminate\.centennialcollege\.ca/ultra/courses/_\d+_1/outline/edit/document/_\d+_1\?courseId=_\d+_1&view=content&state=view$'
    
    if re.match(pattern, url):
        return True, "Valid"
    
    # Detailed error reporting
    if not url.startswith("https://luminate.centennialcollege.ca/ultra/courses/"):
        return False, "Invalid base URL"
    if "/outline/edit/document/" not in url:
        return False, "Missing /outline/edit/document/ path"
    if "?courseId=" not in url:
        return False, "Missing courseId query parameter"
    if "&view=content&state=view" not in url:
        return False, "Missing view and state parameters"
    
    return False, "URL format doesn't match expected pattern"


def analyze_output_directory(output_dir: Path = Path("comp_237_content")):
    """Analyze all JSON files and verify URL formats."""
    
    print("=" * 80)
    print("Blackboard Ultra URL Verification")
    print("=" * 80)
    print(f"Scanning: {output_dir}")
    print()
    
    json_files = list(output_dir.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files")
    print()
    
    stats = {
        "total_documents": 0,
        "documents_with_urls": 0,
        "documents_without_urls": 0,
        "valid_urls": 0,
        "invalid_urls": 0,
        "total_chunks": 0,
        "chunks_with_urls": 0,
        "unique_course_ids": set(),
        "unique_doc_ids": set()
    }
    
    issues = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats["total_documents"] += 1
            
            # Check document-level URL
            doc_url = data.get("live_lms_url")
            bb_doc_id = data.get("bb_doc_id")
            
            if bb_doc_id:
                stats["unique_doc_ids"].add(bb_doc_id)
            
            course_id = data.get("course_id")
            if course_id:
                stats["unique_course_ids"].add(course_id)
            
            if doc_url:
                stats["documents_with_urls"] += 1
                is_valid, message = verify_url_format(doc_url)
                
                if is_valid:
                    stats["valid_urls"] += 1
                else:
                    stats["invalid_urls"] += 1
                    issues.append({
                        "file": json_file.name,
                        "doc_id": bb_doc_id,
                        "url": doc_url,
                        "error": message
                    })
            else:
                stats["documents_without_urls"] += 1
            
            # Check chunk URLs
            chunks = data.get("chunks", [])
            stats["total_chunks"] += len(chunks)
            
            for chunk in chunks:
                chunk_url = chunk.get("live_lms_url")
                if chunk_url:
                    stats["chunks_with_urls"] += 1
                    
                    # Verify chunk URL matches document URL
                    if chunk_url != doc_url:
                        issues.append({
                            "file": json_file.name,
                            "doc_id": bb_doc_id,
                            "url": chunk_url,
                            "error": f"Chunk URL doesn't match document URL"
                        })
        
        except Exception as e:
            issues.append({
                "file": json_file.name,
                "error": f"Error processing file: {e}"
            })
    
    # Print results
    print("📊 STATISTICS")
    print("-" * 80)
    print(f"Documents processed:        {stats['total_documents']}")
    print(f"  ✅ With URLs:             {stats['documents_with_urls']}")
    print(f"  ❌ Without URLs:          {stats['documents_without_urls']}")
    print()
    print(f"URL Validation:")
    print(f"  ✅ Valid URLs:            {stats['valid_urls']}")
    print(f"  ❌ Invalid URLs:          {stats['invalid_urls']}")
    print()
    print(f"Chunks processed:           {stats['total_chunks']}")
    print(f"  ✅ With URLs:             {stats['chunks_with_urls']}")
    print()
    print(f"Unique Course IDs:          {len(stats['unique_course_ids'])}")
    for cid in sorted(stats['unique_course_ids']):
        print(f"  - {cid}")
    print()
    print(f"Unique Document IDs:        {len(stats['unique_doc_ids'])}")
    print()
    
    # Show sample URLs
    print("📋 SAMPLE VALID URLS")
    print("-" * 80)
    sample_count = 0
    for json_file in json_files[:5]:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            url = data.get("live_lms_url")
            if url:
                is_valid, _ = verify_url_format(url)
                if is_valid:
                    print(f"File: {json_file.name}")
                    print(f"  Doc ID: {data.get('bb_doc_id')}")
                    print(f"  Title: {data.get('title', 'N/A')}")
                    print(f"  URL: {url}")
                    print()
                    sample_count += 1
                    if sample_count >= 3:
                        break
        except:
            continue
    
    # Show issues
    if issues:
        print("⚠️  ISSUES FOUND")
        print("-" * 80)
        for issue in issues[:10]:  # Show first 10 issues
            print(f"File: {issue.get('file', 'Unknown')}")
            print(f"  Error: {issue.get('error')}")
            if 'url' in issue:
                print(f"  URL: {issue['url']}")
            print()
        
        if len(issues) > 10:
            print(f"... and {len(issues) - 10} more issues")
    else:
        print("✅ NO ISSUES FOUND - All URLs are valid!")
    
    print()
    print("=" * 80)
    
    # Return success status
    return stats["invalid_urls"] == 0 and len(issues) == 0


def show_url_format_examples():
    """Display URL format examples for reference."""
    print("=" * 80)
    print("BLACKBOARD ULTRA URL FORMAT REFERENCE")
    print("=" * 80)
    print()
    print("✅ CORRECT FORMAT:")
    print("https://luminate.centennialcollege.ca/ultra/courses/{COURSE_ID}/outline/edit/document/{DOC_ID}?courseId={COURSE_ID}&view=content&state=view")
    print()
    print("Example:")
    print("https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view")
    print()
    print("Components:")
    print("  - Base: https://luminate.centennialcollege.ca/ultra/courses")
    print("  - Course ID: _29430_1")
    print("  - Path: /outline/edit/document/")
    print("  - Document ID: _800668_1")
    print("  - Query: ?courseId=_29430_1&view=content&state=view")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    show_url_format_examples()
    success = analyze_output_directory()
    
    exit(0 if success else 1)
