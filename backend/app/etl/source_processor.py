"""
Unified Source Processor

Creates a clean, enriched dataset combining:
1. Course content with clickable Blackboard links
2. Validated external links (YouTube, Mediasite, external resources)
3. Analyzed images with educational context
4. OER supplementary materials
5. All data cleaned of nulls and inconsistencies

Output: data/processed/enriched_sources.json - Ready for ChromaDB ingestion

Usage:
    python -m app.etl.source_processor
"""

import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Input files
CLEANED_CONTENT_FILE = PROCESSED_DIR / "cleaned_content.json"
VALIDATED_LINKS_FILE = PROCESSED_DIR / "validated_links.json"
IMAGES_FILE = PROCESSED_DIR / "images.json"
OER_DIR = RAW_DIR / "oer-sources"
OER_FILES = [
    OER_DIR / "chroma_input.jsonl",
    OER_DIR / "python_chunks.jsonl",
]
BLACKBOARD_CONFIG_FILE = Path(__file__).parent / "blackboard_config.json"
BLACKBOARD_MAPPINGS_FILE = PROCESSED_DIR / "blackboard_mappings.json"
BLACKBOARD_CONTENT_IDS_FILE = PROCESSED_DIR / "blackboard_content_ids.json"

# Output file
OUTPUT_FILE = PROCESSED_DIR / "enriched_sources.json"


class SourceType(str, Enum):
    COURSE_CONTENT = "course_content"
    MEDIASITE_VIDEO = "mediasite_video"
    YOUTUBE_VIDEO = "youtube_video"
    EXTERNAL_RESOURCE = "external_resource"
    IMAGE = "image"
    OER = "oer"


@dataclass
class EnrichedSource:
    """Represents an enriched source for RAG"""
    id: str
    type: SourceType
    title: str
    content: str
    
    # Location context
    module: Optional[int] = None
    week: Optional[int] = None
    topic: Optional[str] = None
    
    # Links
    blackboard_url: Optional[str] = None
    external_url: Optional[str] = None
    
    # Metadata
    concepts: List[str] = None
    keywords: List[str] = None
    source_file: Optional[str] = None
    
    # Quality indicators
    quality_score: int = 0
    is_verified: bool = False
    
    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []
        if self.keywords is None:
            self.keywords = []


class SourceProcessor:
    """Processes and enriches all course sources"""
    
    def __init__(self):
        self.blackboard_config = self._load_blackboard_config()
        self.blackboard_mappings = self._load_json(BLACKBOARD_MAPPINGS_FILE) or {}
        self.blackboard_content_ids = self._load_json(BLACKBOARD_CONTENT_IDS_FILE) or {}
        
        self.results = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "course_content": 0,
                "mediasite_videos": 0,
                "youtube_videos": 0,
                "external_resources": 0,
                "images": 0,
                "oer": 0,
                "total": 0,
                "nulls_cleaned": 0,
                "duplicates_removed": 0,
            },
            "sources": [],
        }
    
    def _load_json(self, path: Path) -> Optional[Dict]:
        """Load JSON file safely"""
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return None
    
    def _load_jsonl(self, path: Path) -> List[Dict]:
        """Load JSONL file safely"""
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []
        
        items = []
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        items.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
        return items
    
    def _load_blackboard_config(self) -> Dict:
        """Load Blackboard configuration"""
        config = self._load_json(BLACKBOARD_CONFIG_FILE)
        if not config:
            return {
                "comp237_course_id": "_11378_1",
                "blackboard_url_pattern": "https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline/edit/document/{CONTENT_ID}?courseId=_11378_1&view=content"
            }
        return config.get("verification", config)
    
    def _generate_blackboard_url(self, resource_id: str) -> Optional[str]:
        """Generate clickable Blackboard URL for a resource"""
        content_info = self.blackboard_content_ids.get(resource_id, {})
        content_id = content_info.get("content_id")
        
        if content_id:
            pattern = self.blackboard_config.get("blackboard_url_pattern", "")
            return pattern.replace("{CONTENT_ID}", content_id)
        return None
    
    def _clean_value(self, value: Any) -> Any:
        """Clean null/empty values recursively"""
        if value is None:
            self.results["summary"]["nulls_cleaned"] += 1
            return None
        
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned or cleaned.lower() in ("null", "none", "n/a", "undefined"):
                self.results["summary"]["nulls_cleaned"] += 1
                return None
            return cleaned
        
        if isinstance(value, list):
            cleaned_list = [self._clean_value(v) for v in value]
            return [v for v in cleaned_list if v is not None]
        
        if isinstance(value, dict):
            return {k: self._clean_value(v) for k, v in value.items() if self._clean_value(v) is not None}
        
        return value
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract AI/ML concepts from text"""
        concept_patterns = {
            "neural_networks": r"\b(neural.?network|ann|perceptron|hidden.?layer|deep.?learning)\b",
            "machine_learning": r"\b(machine.?learning|ml|supervised|unsupervised|reinforcement)\b",
            "classification": r"\b(classif\w+|logistic.?regression|decision.?tree|random.?forest|svm)\b",
            "regression": r"\b(linear.?regression|gradient.?descent|loss.?function|mse)\b",
            "search_algorithms": r"\b(bfs|dfs|breadth.?first|depth.?first|a\*.?search|greedy|heuristic)\b",
            "agents": r"\b(intelligent.?agent|reflex.?agent|goal.?based|utility.?based)\b",
            "nlp": r"\b(natural.?language|nlp|text.?processing|tokeniz\w+|n-?gram)\b",
            "computer_vision": r"\b(computer.?vision|image.?process\w+|opencv|feature.?detect\w+)\b",
            "clustering": r"\b(cluster\w+|k-?means|hierarchical|dbscan)\b",
            "probability": r"\b(probabil\w+|bayes|conditional|prior|posterior)\b",
            "optimization": r"\b(optimi[sz]\w+|gradient|backprop\w+|learning.?rate)\b",
        }
        
        text_lower = text.lower() if text else ""
        found_concepts = []
        
        for concept, pattern in concept_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                found_concepts.append(concept)
        
        return found_concepts
    
    def _hash_id(self, *parts) -> str:
        """Generate deterministic ID from parts"""
        combined = "::".join(str(p) for p in parts if p)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def process_course_content(self) -> List[EnrichedSource]:
        """Process cleaned course content"""
        logger.info("Processing course content...")
        
        data = self._load_json(CLEANED_CONTENT_FILE)
        if not data:
            return []
        
        sources = []
        seen_ids = set()
        
        for item in data:
            # Clean the item
            item = self._clean_value(item)
            if not item:
                continue
            
            resource_id = item.get("resource_id", "")
            content = item.get("content", "")
            
            if not content or len(content) < 50:
                continue
            
            # Skip MP4 files - they can't be used
            if ".mp4" in content.lower() or resource_id.endswith(".mp4"):
                continue
            
            # Generate ID
            source_id = item.get("id") or self._hash_id(resource_id, content[:100])
            
            # Skip duplicates
            if source_id in seen_ids:
                self.results["summary"]["duplicates_removed"] += 1
                continue
            seen_ids.add(source_id)
            
            # Generate Blackboard URL
            bb_url = self._generate_blackboard_url(resource_id)
            
            # Extract concepts
            concepts = item.get("concepts", []) or self._extract_concepts(content)
            
            source = EnrichedSource(
                id=source_id,
                type=SourceType.COURSE_CONTENT,
                title=item.get("title", "Untitled"),
                content=content,
                module=item.get("module") if item.get("module") else self._extract_module(item.get("title", "")),
                week=item.get("week"),
                topic=item.get("topic"),
                blackboard_url=bb_url,
                concepts=concepts,
                keywords=item.get("keywords", []),
                source_file=resource_id,
                quality_score=item.get("quality_score", 50),
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["course_content"] = len(sources)
        logger.info(f"Processed {len(sources)} course content items")
        return sources
    
    def _extract_module(self, title: str) -> Optional[int]:
        """Extract module number from title"""
        match = re.search(r"Module\s*(\d+)", title, re.IGNORECASE)
        return int(match.group(1)) if match else None
    
    def process_validated_links(self) -> List[EnrichedSource]:
        """Process validated external links"""
        logger.info("Processing validated links...")
        
        data = self._load_json(VALIDATED_LINKS_FILE)
        if not data:
            return []
        
        sources = []
        
        # Process Mediasite videos
        for link in data.get("links", {}).get("mediasite", []):
            link = self._clean_value(link)
            if not link:
                continue
            
            url = link.get("url", "")
            context = link.get("context_text", "") or link.get("title", "")
            
            source = EnrichedSource(
                id=self._hash_id("mediasite", url),
                type=SourceType.MEDIASITE_VIDEO,
                title=f"Recorded Lecture: {link.get('title', 'Video')}",
                content=f"Mediasite recorded lecture. {context}. Topics covered: {', '.join(link.get('syllabus_keywords', []))}",
                external_url=url,
                module=link.get("module"),
                week=link.get("week"),
                concepts=self._extract_concepts(context),
                keywords=link.get("syllabus_keywords", []),
                source_file=link.get("source_file"),
                quality_score=80,
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["mediasite_videos"] = len([s for s in sources if s.type == SourceType.MEDIASITE_VIDEO])
        
        # Process YouTube videos
        for link in data.get("links", {}).get("youtube", []):
            link = self._clean_value(link)
            if not link:
                continue
            
            url = link.get("converted_url") or link.get("url", "")
            context = link.get("context_text", "") or link.get("title", "")
            youtube_meta = link.get("youtube_metadata", {})
            
            source = EnrichedSource(
                id=self._hash_id("youtube", youtube_meta.get("video_id", url)),
                type=SourceType.YOUTUBE_VIDEO,
                title=f"YouTube Video: {context[:50]}..." if len(context) > 50 else f"YouTube Video: {context}",
                content=f"Educational YouTube video. {context}",
                external_url=url,
                module=link.get("module"),
                week=link.get("week"),
                concepts=self._extract_concepts(context),
                keywords=link.get("syllabus_keywords", []),
                source_file=link.get("source_file"),
                quality_score=70,
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["youtube_videos"] = len([s for s in sources if s.type == SourceType.YOUTUBE_VIDEO])
        
        # Process external resources (only verified working ones)
        for link in data.get("links", {}).get("external", []):
            link = self._clean_value(link)
            if not link or not link.get("is_valid"):
                continue
            
            url = link.get("url", "")
            context = link.get("context_text", "") or link.get("title", "")
            
            source = EnrichedSource(
                id=self._hash_id("external", url),
                type=SourceType.EXTERNAL_RESOURCE,
                title=f"External Resource: {context[:50]}..." if len(context) > 50 else f"External Resource: {context}",
                content=f"External learning resource: {url}. Context: {context}",
                external_url=url,
                module=link.get("module"),
                week=link.get("week"),
                concepts=self._extract_concepts(context),
                source_file=link.get("source_file"),
                quality_score=60,
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["external_resources"] = len([s for s in sources if s.type == SourceType.EXTERNAL_RESOURCE])
        
        logger.info(f"Processed {len(sources)} validated links")
        return sources
    
    def process_images(self) -> List[EnrichedSource]:
        """Process analyzed images"""
        logger.info("Processing analyzed images...")
        
        data = self._load_json(IMAGES_FILE)
        if not data:
            return []
        
        sources = []
        
        for img in data.get("images", []):
            img = self._clean_value(img)
            if not img:
                continue
            
            # Only include educational images
            if not img.get("is_educational"):
                continue
            
            analysis = img.get("analysis", {})
            context = img.get("context", {})
            
            description = analysis.get("description", "")
            educational_context = analysis.get("educational_context", "")
            concepts = analysis.get("concepts", [])
            key_terms = analysis.get("key_terms", [])
            
            content = f"""
Image: {img.get('filename', 'Unknown')}
Type: {analysis.get('image_type', 'unknown')}
Description: {description}
Educational Context: {educational_context}
Key Terms: {', '.join(key_terms)}
            """.strip()
            
            source = EnrichedSource(
                id=img.get("id") or self._hash_id("image", img.get("path")),
                type=SourceType.IMAGE,
                title=f"Course Image: {analysis.get('image_type', 'Diagram')}",
                content=content,
                module=context.get("module"),
                week=context.get("week"),
                topic=context.get("topic"),
                concepts=concepts,
                keywords=key_terms,
                source_file=img.get("path"),
                quality_score=65,
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["images"] = len(sources)
        logger.info(f"Processed {len(sources)} educational images")
        return sources
    
    def process_oer(self) -> List[EnrichedSource]:
        """Process OER supplementary materials from all OER files"""
        logger.info("Processing OER sources...")
        
        # Load from all OER files
        all_items = []
        for oer_file in OER_FILES:
            items = self._load_jsonl(oer_file)
            if items:
                logger.info(f"  Loaded {len(items)} items from {oer_file.name}")
                all_items.extend(items)
        
        if not all_items:
            logger.warning("No OER sources found")
            return []
        
        sources = []
        
        for item in all_items:
            item = self._clean_value(item)
            if not item:
                continue
            
            content = item.get("text", "")
            if not content or len(content) < 50:
                continue
            
            # Map OER topics to course modules where applicable
            topic = item.get("topic", "")
            subtopic = item.get("subtopic", "")
            
            source = EnrichedSource(
                id=item.get("id") or self._hash_id("oer", content[:100]),
                type=SourceType.OER,
                title=item.get("section_heading", subtopic or topic),
                content=content,
                external_url=item.get("source_url"),
                concepts=self._extract_concepts(content),
                keywords=[topic, subtopic] if subtopic else [topic],
                source_file=item.get("source_title"),
                quality_score=75,
                is_verified=True,
            )
            sources.append(source)
        
        self.results["summary"]["oer"] = len(sources)
        logger.info(f"Processed {len(sources)} OER items")
        return sources
    
    def run(self):
        """Run the full processing pipeline"""
        logger.info("Starting unified source processing...")
        
        all_sources = []
        
        # Process all source types
        all_sources.extend(self.process_course_content())
        all_sources.extend(self.process_validated_links())
        all_sources.extend(self.process_images())
        all_sources.extend(self.process_oer())
        
        # Convert to dicts for JSON serialization
        self.results["sources"] = [asdict(s) for s in all_sources]
        self.results["summary"]["total"] = len(all_sources)
        
        # Save results
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {OUTPUT_FILE}")
        self._print_summary()
    
    def _print_summary(self):
        """Print processing summary"""
        s = self.results["summary"]
        print("\n" + "="*60)
        print("UNIFIED SOURCE PROCESSING SUMMARY")
        print("="*60)
        print(f"Course Content:      {s['course_content']}")
        print(f"Mediasite Videos:    {s['mediasite_videos']}")
        print(f"YouTube Videos:      {s['youtube_videos']}")
        print(f"External Resources:  {s['external_resources']}")
        print(f"Educational Images:  {s['images']}")
        print(f"OER Materials:       {s['oer']}")
        print("-"*40)
        print(f"TOTAL SOURCES:       {s['total']}")
        print("-"*40)
        print(f"Nulls Cleaned:       {s['nulls_cleaned']}")
        print(f"Duplicates Removed:  {s['duplicates_removed']}")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    processor = SourceProcessor()
    processor.run()


if __name__ == "__main__":
    main()
