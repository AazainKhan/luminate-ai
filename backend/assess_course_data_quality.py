#!/usr/bin/env python3
"""
Course Data Quality Assessment & Improvement Script

This script:
1. Analyzes the quality of COMP237 course data
2. Identifies issues and gaps
3. Cleans and enriches data
4. Prepares it for ingestion into ChromaDB (vector) + optional Neo4j (graph)

Run: python assess_course_data_quality.py
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from html import unescape
import hashlib

# Paths
BASE_DIR = Path(__file__).parent
CLEANED_DATA_DIR = BASE_DIR / "cleaned_data"
EXPORT_DIR = CLEANED_DATA_DIR / "ExportFile_COMP237"
OUTPUT_DIR = CLEANED_DATA_DIR / "processed"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class DataQualityAssessor:
    """Assess and improve course data quality"""
    
    def __init__(self):
        self.issues = []
        self.stats = defaultdict(int)
        self.syllabus_map = self._load_syllabus_map()
        self.blackboard_mappings = self._load_blackboard_mappings()
        
    def _load_syllabus_map(self) -> Dict:
        """Load the syllabus structure"""
        path = CLEANED_DATA_DIR / "syllabus_map.json"
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_blackboard_mappings(self) -> Dict:
        """Load Blackboard resource mappings"""
        path = CLEANED_DATA_DIR / "blackboard_mappings.json"
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def get_course_pk1(self) -> str:
        """Extract the Course PK1 ID from res00001.dat"""
        res1_path = EXPORT_DIR / "res00001.dat"
        if not res1_path.exists():
            print(f"⚠️ Warning: {res1_path} not found. Using default course PK1.")
            return "_11378_1"  # Default/Fallback
        
        try:
            with open(res1_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Look for id="_XXXXX_1" pattern in the top-level element
                match = re.search(r'id="(_\d+_1)"', content)
                if match:
                    pk1 = match.group(1)
                    print(f"✅ Found Course PK1: {pk1}")
                    return pk1
        except Exception as e:
            print(f"⚠️ Error reading course PK1: {e}")
        
        return "_11378_1"  # Default/Fallback
    
    def clean_html(self, html: str) -> str:
        """Extract clean text from HTML"""
        if not html:
            return ""
        # Decode HTML entities
        text = unescape(html)
        # Remove script and style tags with content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_links(self, html: str) -> List[Dict]:
        """Extract all links from HTML content"""
        links = []
        # Find href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        for match in re.finditer(href_pattern, html):
            url = match.group(1)
            links.append({
                "url": url,
                "type": self._classify_link(url)
            })
        return links
    
    def _classify_link(self, url: str) -> str:
        """Classify link type"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'mediasite' in url_lower:
            return 'mediasite_video'
        elif url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.ipynb', '.py')):
            return 'code'
        elif 'wikipedia' in url_lower:
            return 'wikipedia'
        elif url_lower.startswith('http'):
            return 'external'
        else:
            return 'internal'
    
    def parse_dat_file(self, filepath: Path) -> Optional[Dict]:
        """Parse a single .dat file and extract structured content"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse as XML
            root = ET.fromstring(content)
            
            # Extract key fields
            data = {
                "resource_id": filepath.stem,
                "filepath": str(filepath),
                "content_id": root.get("id", ""),
                "title": "",
                "body_html": "",
                "body_text": "",
                "links": [],
                "created": "",
                "updated": "",
                "content_type": "",
                "is_available": True,
                "is_folder": False,
                "parent_id": "",
                "module": None,
                "week": None,
                "topic": None,
            }
            
            # Extract title
            title_elem = root.find(".//TITLE")
            if title_elem is not None:
                data["title"] = title_elem.get("value", "")
            
            # Extract body/text
            body_elem = root.find(".//BODY/TEXT")
            if body_elem is not None and body_elem.text:
                data["body_html"] = body_elem.text
                data["body_text"] = self.clean_html(body_elem.text)
                data["links"] = self.extract_links(body_elem.text)
            
            # Extract dates
            created = root.find(".//DATES/CREATED")
            if created is not None:
                data["created"] = created.get("value", "")
            updated = root.find(".//DATES/UPDATED")
            if updated is not None:
                data["updated"] = updated.get("value", "")
            
            # Extract flags
            is_avail = root.find(".//FLAGS/ISAVAILABLE")
            if is_avail is not None:
                data["is_available"] = is_avail.get("value", "").lower() == "true"
            is_folder = root.find(".//FLAGS/ISFOLDER")
            if is_folder is not None:
                data["is_folder"] = is_folder.get("value", "").lower() == "true"
            
            # Extract parent
            parent = root.find(".//PARENTID")
            if parent is not None:
                data["parent_id"] = parent.get("value", parent.text or "")
            
            # Extract content handler
            handler = root.find(".//CONTENTHANDLER")
            if handler is not None:
                data["content_type"] = handler.get("value", "")
            
            # Map to module/week based on title and blackboard mappings
            self._enrich_with_module_info(data)
            
            return data
            
        except ET.ParseError as e:
            self.issues.append(f"XML parse error in {filepath}: {e}")
            self.stats["xml_parse_errors"] += 1
            return None
        except Exception as e:
            self.issues.append(f"Error processing {filepath}: {e}")
            self.stats["other_errors"] += 1
            return None
    
    # Lab tutorial to module mapping based on topic keywords
    LAB_MODULE_MAPPING = {
        # Module 1 - Intro to AI
        "python": (1, "Module 1"),
        "introduction to python": (1, "Module 1"),
        # Module 2 - Agents
        "agents": (2, "Module 2"),
        # Module 3 - Uninformed Search
        "uninformed search": (3, "Module 3"),
        # Module 4 - Informed Search
        "informed search": (4, "Module 4"),
        # Module 5 - Linear Regression
        "linear regression": (5, "Module 5"),
        "random sampling": (5, "Module 5"),
        # Module 6 - Logistic Regression
        "logistic regression": (6, "Module 6"),
        "data pre-processing": (6, "Module 6"),
        # Module 8 - Neural Networks Intro
        "perceptron": (8, "Module 8"),
        "stochastic gradient": (8, "Module 8"),
        # Module 9 - Neural Networks
        "neural network": (9, "Module 9"),
        # Module 10 - NLP Basics
        "nlp": (10, "Module 10"),
        "naive bayes": (10, "Module 10"),
        # Module 11 - NLP Classification
        "nlp and classification": (11, "Module 11"),
        # Module 12 - Computer Vision
        "computer vision": (12, "Module 12"),
        # Module 13 - Ethics
        "ethics": (13, "Module 13"),
        "fairness": (13, "Module 13"),
        "bias": (13, "Module 13"),
        "surveillance": (13, "Module 13"),
        "privacy": (13, "Module 13"),
    }
    
    # Items to exclude from content (templates, admin resources)
    EXCLUDED_TITLES = {
        "topic page", "content-blank", "content", "content-activity", "full-page",
        "overview", "overview-2", "gettingstarted", "readwatch", "participate",
        "wrapup", "icons", "tables", "responsive grid", "typography",
        "colour and highlight", "unit readings", "summary", "introduction",
        "learning outcomes", "integrator course preparation checklist",
        "professor course preparation checklist", "external tools login information",
        "template user guide", "template style guide", "web accessibility",
        "interactive content components", "images and video", "documentation",
        "how to edit a content page", "available layouts", "bolt model",
    }
    
    def _enrich_with_module_info(self, data: Dict):
        """Enrich data with module/week information"""
        resource_id = data["resource_id"]
        title = data["title"]
        title_lower = title.lower() if title else ""
        body_text = data.get("body_text", "").lower()
        
        # Check if this should be excluded (template/admin content)
        if title_lower in self.EXCLUDED_TITLES:
            data["exclude"] = True
            return
        
        # Try blackboard mappings first
        if self.blackboard_mappings:
            content_map = self.blackboard_mappings.get("content_to_module", {})
            if resource_id in content_map:
                mapping = content_map[resource_id]
                if mapping.get("module") and mapping["module"] != "Unknown":
                    data["module"] = mapping.get("module")
                    data["week"] = mapping.get("week")
        
        # Extract from title patterns: "Module XX" or "Topic X.Y"
        if not data.get("module") or data["module"] == "Unknown":
            module_match = re.search(r'Module\s*(\d+)', title, re.IGNORECASE)
            if module_match:
                data["module"] = f"Module {module_match.group(1)}"
                data["week"] = int(module_match.group(1))
            
            topic_match = re.search(r'Topic\s*(\d+)\.(\d+)', title, re.IGNORECASE)
            if topic_match:
                data["module"] = f"Module {topic_match.group(1)}"
                data["week"] = int(topic_match.group(1))
                data["topic"] = f"Topic {topic_match.group(1)}.{topic_match.group(2)}"
        
        # Map lab tutorials and other content based on keywords
        if not data.get("module") or data["module"] == "Unknown":
            combined_text = f"{title_lower} {body_text[:500]}"
            
            for keyword, (week, module) in self.LAB_MODULE_MAPPING.items():
                if keyword in combined_text:
                    data["module"] = module
                    data["week"] = week
                    break
            
            # Handle ethics content - Module 13
            ethics_keywords = ["ethics", "fairness", "bias", "surveillance", "privacy", "moral"]
            if any(kw in combined_text for kw in ethics_keywords):
                data["module"] = "Module 13"
                data["week"] = 13
        
        # Mark as course resources if still unmapped but has useful content
        if not data.get("module") or data["module"] == "Unknown":
            combined_text = f"{title_lower} {body_text[:500]}"
            resource_keywords = ["course outline", "anaconda", "student handbook", "textbook"]
            if any(kw in combined_text for kw in resource_keywords):
                data["module"] = "Course Resources"
                data["week"] = 0
    
    def assess_content_quality(self, data: Dict) -> Dict:
        """Assess quality of a single content item"""
        quality = {
            "score": 0,
            "max_score": 100,
            "issues": [],
            "recommendations": []
        }
        
        # Title quality (20 points)
        title = data.get("title", "")
        if not title:
            quality["issues"].append("Missing title")
        elif title in ["ultraDocumentBody", "ROOT", "--TOP--", "Unknown"]:
            quality["issues"].append(f"Non-descriptive title: {title}")
            quality["score"] += 5
        elif len(title) < 5:
            quality["issues"].append(f"Title too short: {title}")
            quality["score"] += 10
        else:
            quality["score"] += 20
        
        # Content quality (40 points)
        body_text = data.get("body_text", "")
        if not body_text:
            quality["issues"].append("No content body")
        elif len(body_text) < 50:
            quality["issues"].append("Content too short (< 50 chars)")
            quality["score"] += 10
        elif len(body_text) < 200:
            quality["score"] += 25
        else:
            quality["score"] += 40
        
        # Module mapping (20 points)
        if data.get("module") and data["module"] != "Unknown":
            quality["score"] += 20
        else:
            quality["issues"].append("Not mapped to a module")
            quality["recommendations"].append("Map content to appropriate module/week")
        
        # Links/resources (10 points)
        links = data.get("links", [])
        if links:
            quality["score"] += 10
            video_links = [l for l in links if l["type"] in ["youtube", "mediasite_video"]]
            if video_links:
                quality["score"] += 5  # Bonus for video content
        
        # Availability (10 points)
        if data.get("is_available", False):
            quality["score"] += 10
        else:
            quality["issues"].append("Content not available to students")
        
        return quality
    
    def run_assessment(self) -> Dict:
        """Run full data quality assessment"""
        print("🔍 Starting COMP237 Course Data Quality Assessment...")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "course_pk1": self.get_course_pk1(),
            "summary": {},
            "by_module": defaultdict(list),
            "quality_distribution": defaultdict(int),
            "issues_summary": defaultdict(int),
            "content_items": [],
            "recommendations": []
        }
        
        # Process all .dat files
        dat_files = list(EXPORT_DIR.glob("res*.dat"))
        print(f"📁 Found {len(dat_files)} .dat files to process")
        
        total_score = 0
        processed = 0
        
        for filepath in dat_files:
            data = self.parse_dat_file(filepath)
            if not data:
                continue
            
            # Skip non-content items
            if data.get("is_folder") or not data.get("body_text"):
                self.stats["skipped_folders"] += 1
                continue
            
            # Assess quality
            quality = self.assess_content_quality(data)
            data["quality"] = quality
            
            # Categorize by quality
            if quality["score"] >= 80:
                results["quality_distribution"]["excellent"] += 1
            elif quality["score"] >= 60:
                results["quality_distribution"]["good"] += 1
            elif quality["score"] >= 40:
                results["quality_distribution"]["fair"] += 1
            else:
                results["quality_distribution"]["poor"] += 1
            
            # Track issues
            for issue in quality["issues"]:
                results["issues_summary"][issue] += 1
            
            # Group by module
            module = data.get("module") or "Unmapped"
            results["by_module"][module].append({
                "resource_id": data["resource_id"],
                "title": data["title"],
                "quality_score": quality["score"],
                "issues": quality["issues"]
            })
            
            results["content_items"].append(data)
            total_score += quality["score"]
            processed += 1
        
        # Calculate summary stats
        avg_score = total_score / processed if processed > 0 else 0
        results["summary"] = {
            "total_files": len(dat_files),
            "processed": processed,
            "skipped": self.stats["skipped_folders"],
            "parse_errors": self.stats["xml_parse_errors"],
            "average_quality_score": round(avg_score, 2),
            "quality_grade": self._score_to_grade(avg_score)
        }
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on assessment"""
        recs = []
        
        issues = results["issues_summary"]
        
        if issues.get("Not mapped to a module", 0) > 10:
            recs.append("HIGH PRIORITY: Many items not mapped to modules. Update blackboard_mappings.json or improve module detection logic.")
        
        if issues.get("No content body", 0) > 5:
            recs.append("Some items have no content - these may be structural elements that can be filtered out.")
        
        if issues.get("Non-descriptive title", 0) > 5:
            recs.append("Clean up non-descriptive titles (ultraDocumentBody, ROOT, etc.) - these pollute search results.")
        
        poor = results["quality_distribution"].get("poor", 0)
        if poor > 10:
            recs.append(f"ATTENTION: {poor} items have poor quality scores. Review and enrich these before ingestion.")
        
        return recs


class CourseDataCleaner:
    """Clean and prepare course data for ingestion"""
    
    # Concept tags for GraphRAG
    CONCEPT_PATTERNS = {
        "artificial_intelligence": r"\b(artificial intelligence|AI|intelligent system)\b",
        "machine_learning": r"\b(machine learning|ML|supervised learning|unsupervised)\b",
        "neural_network": r"\b(neural network|ANN|perceptron|neuron)\b",
        "deep_learning": r"\b(deep learning|CNN|RNN|transformer)\b",
        "search_algorithms": r"\b(search algorithm|DFS|BFS|A\*|heuristic|uninformed search|informed search)\b",
        "classification": r"\b(classification|classifier|logistic regression|decision tree)\b",
        "regression": r"\b(regression|linear regression|MSE|loss function)\b",
        "nlp": r"\b(NLP|natural language|text processing|tokenization|stemming)\b",
        "computer_vision": r"\b(computer vision|image processing|CNN|convolution)\b",
        "gradient_descent": r"\b(gradient descent|optimization|learning rate|backpropagation)\b",
        "probability": r"\b(probability|Bayes|conditional|prior|posterior)\b",
        "agents": r"\b(intelligent agent|rational agent|environment|PEAS)\b",
        "activation_functions": r"\b(activation function|sigmoid|ReLU|tanh|softmax)\b",
        "evaluation": r"\b(confusion matrix|precision|recall|F1|accuracy|cross-validation)\b",
        "data_preprocessing": r"\b(preprocessing|normalization|feature engineering|encoding)\b",
    }
    
    def __init__(self, assessment_results: Dict):
        self.results = assessment_results
        self.cleaned_data = []
    
    def detect_concepts(self, text: str) -> List[str]:
        """Detect AI/ML concepts in text"""
        concepts = []
        text_lower = text.lower()
        for concept, pattern in self.CONCEPT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                concepts.append(concept)
        return concepts
    
    def clean_and_enrich(self) -> List[Dict]:
        """Clean and enrich all content items"""
        print("\n🧹 Cleaning and enriching course data...")
        
        for item in self.results["content_items"]:
            # Skip low-quality items
            if item["quality"]["score"] < 30:
                continue
            
            # Skip excluded items (templates, admin content)
            if item.get("exclude"):
                continue
            
            # Skip non-descriptive titles
            if item["title"] in ["ultraDocumentBody", "ROOT", "--TOP--", ""]:
                continue
            
            # Construct Blackboard Ultra URL
            course_pk1 = self.results.get("course_pk1", "_11378_1")
            content_id = item.get("content_id", "")
            
            # Default URL (generic)
            url = f"https://luminate.centennialcollege.ca/ultra/courses/{course_pk1}/cl/outline"
            
            # Specific Deep Link
            if content_id and content_id.startswith("_"):
                url = f"https://luminate.centennialcollege.ca/ultra/courses/{course_pk1}/outline/edit/document/{content_id}?courseId={course_pk1}&view=content&state=view"

            # Create clean document
            doc = {
                "id": self._generate_id(item),
                "resource_id": item["resource_id"],
                "title": item["title"],
                "content": item["body_text"],
                "module": item.get("module"),
                "week": item.get("week"),
                "topic": item.get("topic"),
                "concepts": self.detect_concepts(item["body_text"]),
                "links": item.get("links", []),
                "quality_score": item["quality"]["score"],
                "content_type": self._classify_content_type(item),
                "metadata": {
                    "course_id": "COMP237",
                    "source": "blackboard_export",
                    "url": url,
                    "content_id": content_id,
                    "created": item.get("created"),
                    "updated": item.get("updated"),
                }
            }
            
            # Chunk large content
            if len(doc["content"]) > 1500:
                chunks = self._chunk_content(doc)
                self.cleaned_data.extend(chunks)
            else:
                self.cleaned_data.append(doc)
        
        print(f"✅ Produced {len(self.cleaned_data)} clean documents")
        return self.cleaned_data
    
    def _generate_id(self, item: Dict) -> str:
        """Generate unique document ID"""
        content = f"{item['resource_id']}:{item['title']}:{item.get('body_text', '')[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _classify_content_type(self, item: Dict) -> str:
        """Classify content type"""
        title_lower = item.get("title", "").lower()
        
        if "lab" in title_lower or "tutorial" in title_lower:
            return "lab_tutorial"
        elif "topic" in title_lower:
            return "topic_content"
        elif "overview" in title_lower:
            return "module_overview"
        elif "assignment" in title_lower:
            return "assignment"
        elif "quiz" in title_lower or "test" in title_lower:
            return "assessment"
        else:
            return "course_content"
    
    def _chunk_content(self, doc: Dict, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Chunk large content with overlap"""
        content = doc["content"]
        chunks = []
        
        start = 0
        chunk_idx = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk_text.rfind('. ')
                if last_period > chunk_size * 0.5:
                    chunk_text = chunk_text[:last_period + 1]
                    end = start + last_period + 1
            
            chunk_doc = doc.copy()
            chunk_doc["id"] = f"{doc['id']}_chunk{chunk_idx}"
            chunk_doc["content"] = chunk_text.strip()
            chunk_doc["metadata"] = doc["metadata"].copy()
            chunk_doc["metadata"]["chunk_index"] = chunk_idx
            chunk_doc["metadata"]["is_chunked"] = True
            
            chunks.append(chunk_doc)
            
            start = end - overlap
            chunk_idx += 1
        
        return chunks


class KnowledgeGraphBuilder:
    """Build concept relationships for GraphRAG"""
    
    # COMP237 concept hierarchy
    CONCEPT_HIERARCHY = {
        "artificial_intelligence": {
            "children": ["machine_learning", "search_algorithms", "agents", "nlp", "computer_vision"],
            "prerequisites": []
        },
        "machine_learning": {
            "children": ["classification", "regression", "neural_network", "evaluation"],
            "prerequisites": ["artificial_intelligence", "probability"]
        },
        "neural_network": {
            "children": ["deep_learning", "activation_functions", "gradient_descent"],
            "prerequisites": ["machine_learning", "classification"]
        },
        "gradient_descent": {
            "children": [],
            "prerequisites": ["neural_network", "regression"]
        },
        "search_algorithms": {
            "children": [],
            "prerequisites": ["artificial_intelligence", "agents"]
        },
        "nlp": {
            "children": [],
            "prerequisites": ["machine_learning", "probability"]
        },
        "classification": {
            "children": ["evaluation"],
            "prerequisites": ["machine_learning", "data_preprocessing"]
        },
        "regression": {
            "children": [],
            "prerequisites": ["machine_learning", "data_preprocessing"]
        },
    }
    
    def build_concept_graph(self, cleaned_data: List[Dict]) -> Dict:
        """Build concept graph from cleaned data"""
        print("\n🕸️ Building concept knowledge graph...")
        
        graph = {
            "nodes": [],
            "edges": [],
            "concept_documents": defaultdict(list)
        }
        
        # Create concept nodes
        concepts_found = set()
        for doc in cleaned_data:
            for concept in doc.get("concepts", []):
                concepts_found.add(concept)
                graph["concept_documents"][concept].append(doc["id"])
        
        # Add concept nodes with metadata
        for concept in concepts_found:
            node = {
                "id": concept,
                "type": "concept",
                "label": concept.replace("_", " ").title(),
                "document_count": len(graph["concept_documents"][concept]),
                "hierarchy_info": self.CONCEPT_HIERARCHY.get(concept, {})
            }
            graph["nodes"].append(node)
        
        # Add hierarchy edges
        for concept, info in self.CONCEPT_HIERARCHY.items():
            if concept not in concepts_found:
                continue
            
            # Parent-child relationships
            for child in info.get("children", []):
                if child in concepts_found:
                    graph["edges"].append({
                        "source": concept,
                        "target": child,
                        "type": "HAS_SUBTOPIC"
                    })
            
            # Prerequisite relationships
            for prereq in info.get("prerequisites", []):
                if prereq in concepts_found:
                    graph["edges"].append({
                        "source": prereq,
                        "target": concept,
                        "type": "PREREQUISITE_FOR"
                    })
        
        # Add document-concept edges
        for concept, doc_ids in graph["concept_documents"].items():
            for doc_id in doc_ids:
                graph["edges"].append({
                    "source": doc_id,
                    "target": concept,
                    "type": "COVERS_CONCEPT"
                })
        
        print(f"✅ Graph built: {len(graph['nodes'])} concept nodes, {len(graph['edges'])} edges")
        return graph


def print_assessment_report(results: Dict):
    """Print formatted assessment report"""
    print("\n" + "=" * 60)
    print("📊 COMP237 DATA QUALITY ASSESSMENT REPORT")
    print("=" * 60)
    
    summary = results["summary"]
    print(f"\n📁 FILES PROCESSED")
    print(f"   Total .dat files: {summary['total_files']}")
    print(f"   Content items: {summary['processed']}")
    print(f"   Skipped (folders): {summary['skipped']}")
    print(f"   Parse errors: {summary['parse_errors']}")
    
    print(f"\n📈 QUALITY METRICS")
    print(f"   Average Score: {summary['average_quality_score']}/100")
    print(f"   Grade: {summary['quality_grade']}")
    
    dist = results["quality_distribution"]
    print(f"\n📊 QUALITY DISTRIBUTION")
    print(f"   Excellent (80-100): {dist.get('excellent', 0)}")
    print(f"   Good (60-79): {dist.get('good', 0)}")
    print(f"   Fair (40-59): {dist.get('fair', 0)}")
    print(f"   Poor (0-39): {dist.get('poor', 0)}")
    
    print(f"\n⚠️ TOP ISSUES")
    for issue, count in sorted(results["issues_summary"].items(), key=lambda x: -x[1])[:5]:
        print(f"   {count}x - {issue}")
    
    print(f"\n📚 CONTENT BY MODULE")
    for module, items in sorted(results["by_module"].items()):
        avg_score = sum(i["quality_score"] for i in items) / len(items) if items else 0
        print(f"   {module}: {len(items)} items (avg score: {avg_score:.1f})")
    
    if results["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS")
        for rec in results["recommendations"]:
            print(f"   • {rec}")


def main():
    """Run complete data quality pipeline"""
    print("🚀 COMP237 Course Data Quality Pipeline")
    print("=" * 60)
    
    # Step 1: Assess data quality
    assessor = DataQualityAssessor()
    results = assessor.run_assessment()
    print_assessment_report(results)
    
    # Save assessment results
    assessment_path = OUTPUT_DIR / "quality_assessment.json"
    with open(assessment_path, 'w') as f:
        # Convert defaultdicts to regular dicts for JSON serialization
        export_results = {
            "timestamp": results["timestamp"],
            "summary": results["summary"],
            "quality_distribution": dict(results["quality_distribution"]),
            "issues_summary": dict(results["issues_summary"]),
            "by_module": {k: v for k, v in results["by_module"].items()},
            "recommendations": results["recommendations"]
        }
        json.dump(export_results, f, indent=2)
    print(f"\n💾 Assessment saved to: {assessment_path}")
    
    # Step 2: Clean and enrich data
    cleaner = CourseDataCleaner(results)
    cleaned_data = cleaner.clean_and_enrich()
    
    # Save cleaned data for ChromaDB ingestion
    cleaned_path = OUTPUT_DIR / "cleaned_content.json"
    with open(cleaned_path, 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    print(f"💾 Cleaned data saved to: {cleaned_path}")
    
    # Step 3: Build concept graph for GraphRAG
    graph_builder = KnowledgeGraphBuilder()
    concept_graph = graph_builder.build_concept_graph(cleaned_data)
    
    # Save concept graph
    graph_path = OUTPUT_DIR / "concept_graph.json"
    with open(graph_path, 'w') as f:
        json.dump({
            "nodes": concept_graph["nodes"],
            "edges": concept_graph["edges"],
            "concept_documents": dict(concept_graph["concept_documents"])
        }, f, indent=2)
    print(f"💾 Concept graph saved to: {graph_path}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("✅ DATA QUALITY PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\n📦 OUTPUT FILES:")
    print(f"   1. {assessment_path.name} - Quality assessment report")
    print(f"   2. {cleaned_path.name} - Cleaned content for ChromaDB")
    print(f"   3. {graph_path.name} - Concept graph for GraphRAG")
    
    print(f"\n🔜 NEXT STEPS:")
    print("   1. Review quality_assessment.json for issues")
    print("   2. Run ChromaDB ingestion: python ingest_cleaned_data.py")
    print("   3. (Optional) Load concept_graph.json into Neo4j for GraphRAG")
    print("   4. Update knowledge_graph.py with concept relationships")
    
    return results, cleaned_data, concept_graph


if __name__ == "__main__":
    main()
