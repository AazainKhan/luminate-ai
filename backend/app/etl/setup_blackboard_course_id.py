#!/usr/bin/env python3
"""
Quick setup script to configure COMP237 Blackboard course ID
Run this before enriching URLs with Blackboard links
"""

import sys
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "enrich_blackboard_urls.py"

def validate_course_id(course_id: str) -> bool:
    """Validate Blackboard course ID format"""
    # Format: _XXXXX_1 where XXXXX is 5+ digits
    pattern = r'^_\d{5,}_1$'
    return bool(re.match(pattern, course_id))

def update_course_id(course_id: str):
    """Update course ID in enrich_blackboard_urls.py"""
    print(f"📝 Updating course ID to: {course_id}")
    
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()
    
    # Replace the placeholder
    updated = re.sub(
        r'COMP237_COURSE_ID = "[^"]*"',
        f'COMP237_COURSE_ID = "{course_id}"',
        content
    )
    
    with open(SCRIPT_PATH, 'w') as f:
        f.write(updated)
    
    print(f"✅ Course ID updated in: {SCRIPT_PATH}")

def main():
    print("=" * 60)
    print("🎓 COMP237 Blackboard Course ID Setup")
    print("=" * 60)
    print()
    
    # Instructions
    print("To find your course ID:")
    print("1. Go to COMP237 in Blackboard Ultra")
    print("2. Click on any content item")
    print("3. Look at the browser URL:")
    print("   https://luminate.centennialcollege.ca/ultra/courses/_XXXXX_1/...")
    print("4. Copy the '_XXXXX_1' part (e.g., '_29430_1')")
    print()
    
    # Get input
    if len(sys.argv) > 1:
        course_id = sys.argv[1]
    else:
        course_id = input("Enter COMP237 course ID (e.g., _29430_1): ").strip()
    
    # Validate
    if not course_id:
        print("❌ Error: No course ID provided")
        sys.exit(1)
    
    if not validate_course_id(course_id):
        print(f"❌ Error: Invalid course ID format: {course_id}")
        print("   Expected format: _XXXXX_1 (e.g., _29430_1)")
        sys.exit(1)
    
    # Update
    update_course_id(course_id)
    
    print()
    print("✅ Setup complete!")
    print()
    print("Next steps:")
    print("1. Run enrichment:")
    print("   docker exec api_brain python -m app.etl.enrich_blackboard_urls \\")
    print("     --content-ids-path /app/data/processed/blackboard_content_ids.json")
    print()
    print("2. Verify:")
    print("   docker exec api_brain python -m app.etl.enrich_blackboard_urls \\")
    print("     --stats-only --course-id " + course_id)
    print()

if __name__ == "__main__":
    main()
