"""
Link Validator Script

Validates all external links extracted from course materials:
1. Tests if links are reachable (HTTP 200)
2. Categorizes links by type (mediasite, youtube, external)
3. Converts embed URLs to proper clickable links
4. Removes broken links and maps working ones with context

Usage:
    python -m app.etl.link_validator
"""

import json
import logging
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "validated_links.json"


class LinkValidator:
    """Validates and enriches external links from course materials"""
    
    # Trusted domains that should always work (skip validation)
    TRUSTED_DOMAINS = {
        "mediasite.centennialcollege.ca",
        "youtube.com",
        "youtu.be",
        "www.youtube.com",
    }
    
    # YouTube embed URL patterns
    YOUTUBE_EMBED_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"
    )
    
    # Blackboard internal link patterns (should be converted)
    BLACKBOARD_INTERNAL_PATTERNS = [
        r"@X@EmbeddedFile\.requestUrlStub@X@",
        r"bbcswebdav/",
        r"/xid-\d+",
    ]
    
    def __init__(self):
        self.results = {
            "validated_at": datetime.now().isoformat(),
            "summary": {
                "total_links": 0,
                "valid_links": 0,
                "broken_links": 0,
                "converted_links": 0,
                "mediasite_links": 0,
                "youtube_links": 0,
                "external_links": 0,
                "skipped_internal": 0,
            },
            "links": {
                "mediasite": [],
                "youtube": [],
                "external": [],
                "broken": [],
                "internal_skipped": [],
            }
        }
    
    def convert_youtube_embed_to_watch(self, embed_url: str) -> str:
        """
        Convert YouTube embed URL to regular watch URL
        
        Examples:
            https://www.youtube.com/embed/Kd3fApWbNyo -> https://www.youtube.com/watch?v=Kd3fApWbNyo
            https://www.youtube.com/embed/XepXtl9YKwc?wmode=opaque -> https://www.youtube.com/watch?v=XepXtl9YKwc
        """
        match = self.YOUTUBE_EMBED_PATTERN.search(embed_url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        return embed_url
    
    def is_internal_blackboard_link(self, url: str) -> bool:
        """Check if URL is an internal Blackboard link that can't be opened externally"""
        for pattern in self.BLACKBOARD_INTERNAL_PATTERNS:
            if re.search(pattern, url):
                return True
        return False
    
    def categorize_link(self, url: str) -> str:
        """Categorize a link by its type"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if "mediasite" in domain:
            return "mediasite"
        elif "youtube" in domain or "youtu.be" in domain:
            return "youtube"
        elif self.is_internal_blackboard_link(url):
            return "internal"
        else:
            return "external"
    
    def extract_youtube_metadata(self, url: str) -> Dict:
        """Extract metadata from YouTube URL"""
        watch_url = self.convert_youtube_embed_to_watch(url)
        parsed = urlparse(watch_url)
        
        # Extract video ID
        video_id = None
        if "youtube.com" in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
        elif "youtu.be" in parsed.netloc:
            video_id = parsed.path.strip("/")
        
        return {
            "original_url": url,
            "watch_url": watch_url,
            "video_id": video_id,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None,
            "is_embed": "/embed/" in url,
        }
    
    def extract_mediasite_metadata(self, url: str) -> Dict:
        """Extract metadata from Mediasite URL"""
        # Mediasite URLs typically have a GUID in them
        # Example: https://mediasite.centennialcollege.ca/Mediasite/Play/51657db5d9af417cb3df6c8ae75715261d
        parsed = urlparse(url)
        path_parts = parsed.path.split("/")
        
        presentation_id = None
        if "Play" in path_parts:
            play_index = path_parts.index("Play")
            if play_index + 1 < len(path_parts):
                presentation_id = path_parts[play_index + 1]
        
        return {
            "url": url,
            "presentation_id": presentation_id,
            "type": "recorded_lecture",
        }
    
    async def validate_url(self, session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Tuple[bool, int, str]:
        """
        Validate if a URL is reachable
        
        Returns:
            Tuple of (is_valid, status_code, error_message)
        """
        try:
            # Skip validation for trusted domains
            parsed = urlparse(url)
            if parsed.netloc.lower() in self.TRUSTED_DOMAINS:
                return (True, 200, "Trusted domain - skipped validation")
            
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as response:
                is_valid = response.status < 400
                return (is_valid, response.status, "" if is_valid else f"HTTP {response.status}")
        except asyncio.TimeoutError:
            return (False, 0, "Timeout")
        except aiohttp.ClientError as e:
            return (False, 0, str(e))
        except Exception as e:
            return (False, 0, str(e))
    
    async def validate_links_batch(self, links: List[Dict], batch_size: int = 20) -> List[Dict]:
        """Validate a batch of links concurrently"""
        validated = []
        
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (compatible; COMP237-LinkValidator/1.0)"}
        ) as session:
            for i in range(0, len(links), batch_size):
                batch = links[i:i + batch_size]
                tasks = []
                
                for link in batch:
                    url = link.get("url", "")
                    category = self.categorize_link(url)
                    
                    # Skip internal Blackboard links
                    if category == "internal":
                        link["status"] = "skipped"
                        link["reason"] = "Internal Blackboard link"
                        validated.append(link)
                        continue
                    
                    # Convert YouTube embeds
                    if category == "youtube":
                        youtube_meta = self.extract_youtube_metadata(url)
                        link["youtube_metadata"] = youtube_meta
                        link["converted_url"] = youtube_meta["watch_url"]
                        url = youtube_meta["watch_url"]
                    
                    # Extract Mediasite metadata
                    if category == "mediasite":
                        link["mediasite_metadata"] = self.extract_mediasite_metadata(url)
                    
                    link["category"] = category
                    tasks.append((link, self.validate_url(session, url)))
                
                # Run validations concurrently
                if tasks:
                    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
                    
                    for (link, _), result in zip(tasks, results):
                        if isinstance(result, Exception):
                            link["is_valid"] = False
                            link["error"] = str(result)
                        else:
                            is_valid, status_code, error = result
                            link["is_valid"] = is_valid
                            link["status_code"] = status_code
                            if error:
                                link["error"] = error
                        validated.append(link)
                
                logger.info(f"Validated batch {i//batch_size + 1}: {len(validated)} total")
        
        return validated
    
    def load_embedded_content(self) -> List[Dict]:
        """Load links from embedded_content.json"""
        embedded_file = PROCESSED_DIR / "embedded_content.json"
        if not embedded_file.exists():
            logger.warning(f"embedded_content.json not found at {embedded_file}")
            return []
        
        with open(embedded_file, "r") as f:
            data = json.load(f)
        
        links = []
        for item in data.get("embedded_items", []):
            course_location = item.get("course_location", {})
            
            for link in item.get("extracted_links", []):
                links.append({
                    "url": link.get("url"),
                    "link_type": link.get("type"),
                    "context_text": link.get("context_text", ""),
                    "source_file": item.get("source_file"),
                    "resource_id": item.get("associated_resource_id"),
                    "parent": course_location.get("parent", ""),
                    "title": course_location.get("title", ""),
                    "syllabus_keywords": course_location.get("syllabus_keywords", []),
                })
        
        return links
    
    def load_cleaned_content_links(self) -> List[Dict]:
        """Load links from cleaned_content.json"""
        cleaned_file = PROCESSED_DIR / "cleaned_content.json"
        if not cleaned_file.exists():
            logger.warning(f"cleaned_content.json not found at {cleaned_file}")
            return []
        
        with open(cleaned_file, "r") as f:
            data = json.load(f)
        
        links = []
        for item in data:
            for link in item.get("links", []):
                url = link.get("url", "")
                # Skip internal blackboard links
                if not url.startswith("http"):
                    continue
                    
                links.append({
                    "url": url,
                    "link_type": link.get("type"),
                    "context_text": item.get("title", ""),
                    "content_preview": item.get("content", "")[:200] if item.get("content") else "",
                    "resource_id": item.get("resource_id"),
                    "module": item.get("module"),
                    "week": item.get("week"),
                    "concepts": item.get("concepts", []),
                })
        
        return links
    
    def deduplicate_links(self, links: List[Dict]) -> List[Dict]:
        """Remove duplicate links, keeping the one with most context"""
        seen = {}
        
        for link in links:
            url = link.get("url", "")
            if not url:
                continue
            
            # Normalize URL for deduplication
            normalized = url.lower().rstrip("/")
            
            if normalized not in seen:
                seen[normalized] = link
            else:
                # Keep the link with more context
                existing = seen[normalized]
                if len(link.get("context_text", "")) > len(existing.get("context_text", "")):
                    seen[normalized] = link
        
        return list(seen.values())
    
    async def run(self):
        """Run the full validation pipeline"""
        logger.info("Loading links from embedded_content.json and cleaned_content.json...")
        
        # Load links from both sources
        embedded_links = self.load_embedded_content()
        cleaned_links = self.load_cleaned_content_links()
        
        all_links = embedded_links + cleaned_links
        logger.info(f"Found {len(all_links)} total links")
        
        # Deduplicate
        unique_links = self.deduplicate_links(all_links)
        logger.info(f"After deduplication: {len(unique_links)} unique links")
        
        self.results["summary"]["total_links"] = len(unique_links)
        
        # Validate links
        logger.info("Validating links...")
        validated_links = await self.validate_links_batch(unique_links)
        
        # Categorize results
        for link in validated_links:
            category = link.get("category", "external")
            is_valid = link.get("is_valid", False)
            status = link.get("status", "")
            
            if status == "skipped":
                self.results["links"]["internal_skipped"].append(link)
                self.results["summary"]["skipped_internal"] += 1
            elif is_valid:
                self.results["links"][category].append(link)
                self.results["summary"]["valid_links"] += 1
                self.results["summary"][f"{category}_links"] += 1
                
                # Track converted links
                if link.get("converted_url"):
                    self.results["summary"]["converted_links"] += 1
            else:
                self.results["links"]["broken"].append(link)
                self.results["summary"]["broken_links"] += 1
        
        # Save results
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {OUTPUT_FILE}")
        self._print_summary()
    
    def _print_summary(self):
        """Print validation summary"""
        s = self.results["summary"]
        print("\n" + "="*60)
        print("LINK VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Links:         {s['total_links']}")
        print(f"Valid Links:         {s['valid_links']}")
        print(f"Broken Links:        {s['broken_links']}")
        print(f"Converted (embed→watch): {s['converted_links']}")
        print("-"*40)
        print(f"Mediasite (lectures): {s['mediasite_links']}")
        print(f"YouTube:             {s['youtube_links']}")
        print(f"External:            {s['external_links']}")
        print(f"Internal (skipped):  {s['skipped_internal']}")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    validator = LinkValidator()
    asyncio.run(validator.run())


if __name__ == "__main__":
    main()
