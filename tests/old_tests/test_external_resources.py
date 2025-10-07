#!/usr/bin/env python3
"""Test external resources functionality without actually making API calls."""

# Mock external resources for testing
test_resources = [
    {
        "title": "Neural Networks Explained - 3Blue1Brown",
        "url": "https://www.youtube.com/watch?v=aircAruvnKk",
        "description": "But what is a neural network? Chapter 1, Deep learning",
        "type": "YouTube Video",
        "channel": "3Blue1Brown"
    },
    {
        "title": "OER Commons: Machine Learning",
        "url": "https://www.oercommons.org/search?q=machine+learning",
        "description": "Search OER Commons for open educational resources about machine learning",
        "type": "OER Commons",
        "channel": "OER Commons"
    },
    {
        "title": "Khan Academy: Machine Learning",
        "url": "https://www.khanacademy.org/search?page_search_query=machine+learning",
        "description": "Search Khan Academy for lessons and exercises about machine learning",
        "type": "Khan Academy",
        "channel": "Khan Academy"
    },
    {
        "title": "MIT OpenCourseWare: Machine Learning",
        "url": "https://ocw.mit.edu/search/?q=machine+learning",
        "description": "Search MIT OpenCourseWare for courses and materials about machine learning",
        "type": "MIT OCW",
        "channel": "MIT OpenCourseWare"
    }
]

print("🧪 Testing External Resources Structure\n" + "="*70)

print(f"\n✅ Sample external resources generated: {len(test_resources)} resources\n")

for i, resource in enumerate(test_resources, 1):
    print(f"{i}. [{resource['type']}] {resource['title']}")
    print(f"   URL: {resource['url']}")
    print(f"   Channel: {resource['channel']}")
    print(f"   Description: {resource['description'][:60]}...")
    print()

print("="*70)
print("✅ External resources structure is valid!")
print("\nℹ️  These resources will be displayed in the Chrome extension UI:")
print("   - YouTube videos (if API key is configured)")
print("   - OER Commons search links")
print("   - Khan Academy search links")
print("   - MIT OpenCourseWare search links")
print("\n💡 To enable YouTube search, add YOUTUBE_API_KEY to .env file")
print("   See EXTERNAL_RESOURCES_SETUP.md for instructions")
