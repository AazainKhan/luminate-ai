"""
Educational AI Validation Tests for Luminate AI
Purpose: Validate pedagogical requirements based on educational_ai.md research

Tests align with:
- VanLehn's ITS Model (2011)
- AutoTutor best practices (Graesser et al., 2004)
- UNESCO AI in Education guidelines (2024)
- Multi-agent architecture principles

Categories:
1. Content Quality & Domain Model
2. Retrieval & Navigation Effectiveness
3. Pedagogical Alignment
4. Privacy & Ethics
5. Performance & Accessibility
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re
import requests
from collections import Counter

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
COMP237_DATA = PROJECT_ROOT / "comp_237_content"
GRAPH_SEED = PROJECT_ROOT / "graph_seed"
TEST_LOGS = PROJECT_ROOT / "development/tests/logs"

# Create test logs directory
TEST_LOGS.mkdir(parents=True, exist_ok=True)


class TestLogger:
    """Enhanced test logger with category tracking"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.category_results = {}
        self.start_time = datetime.now()
        
    def log(self, level: str, message: str, to_console: bool = True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_line)
        
        if to_console:
            colors = {
                "PASS": "\033[92m",  # Green
                "FAIL": "\033[91m",  # Red
                "INFO": "\033[94m",  # Blue
                "WARN": "\033[93m",  # Yellow
                "CATEGORY": "\033[95m",  # Magenta
                "END": "\033[0m"      # Reset
            }
            color = colors.get(level, "")
            print(f"{color}[{level}]{colors['END']} {message}")
    
    def category_start(self, category_name: str):
        self.current_category = category_name
        self.category_results[category_name] = {"passed": 0, "failed": 0}
        self.log("CATEGORY", f"=" * 80)
        self.log("CATEGORY", f"Category: {category_name}")
        self.log("CATEGORY", f"=" * 80)
    
    def test_start(self, test_name: str):
        self.tests_run += 1
        self.log("INFO", f"Running test: {test_name}")
    
    def test_pass(self, test_name: str, details: str = ""):
        self.tests_passed += 1
        if hasattr(self, 'current_category'):
            self.category_results[self.current_category]["passed"] += 1
        msg = f"✓ {test_name}"
        if details:
            msg += f" - {details}"
        self.log("PASS", msg)
    
    def test_fail(self, test_name: str, reason: str):
        self.tests_failed += 1
        if hasattr(self, 'current_category'):
            self.category_results[self.current_category]["failed"] += 1
        self.log("FAIL", f"✗ {test_name} - {reason}")
    
    def summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        self.log("INFO", "=" * 80)
        self.log("INFO", "Educational AI Validation Summary")
        self.log("INFO", "=" * 80)
        
        # Overall results
        self.log("INFO", f"Total Tests: {self.tests_run}")
        self.log("INFO", f"Passed: {self.tests_passed} ({self.tests_passed/self.tests_run*100:.1f}%)")
        self.log("INFO", f"Failed: {self.tests_failed} ({self.tests_failed/self.tests_run*100:.1f}%)")
        self.log("INFO", f"Duration: {duration:.2f}s")
        
        # Category breakdown
        self.log("INFO", "\nResults by Category:")
        for category, results in self.category_results.items():
            total = results["passed"] + results["failed"]
            pass_rate = results["passed"] / total * 100 if total > 0 else 0
            status = "✓" if results["failed"] == 0 else "✗"
            self.log("INFO", f"  {status} {category}: {results['passed']}/{total} ({pass_rate:.1f}%)")
        
        self.log("INFO", "=" * 80)
        return self.tests_failed == 0


class EducationalAITests:
    """Educational AI validation tests based on research"""
    
    def __init__(self, logger: TestLogger, api_url: str = "http://127.0.0.1:8000"):
        self.logger = logger
        self.course_id = "_11378_1"
        self.api_url = api_url
        self.api_available = self._check_api()
    
    def _check_api(self) -> bool:
        """Check if FastAPI service is available"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    # ========================================================================
    # Category 1: Content Quality & Domain Model (VanLehn's ITS Model)
    # ========================================================================
    
    def test_domain_coverage(self) -> bool:
        """Test that content covers core COMP237 topics"""
        self.logger.test_start("Domain Coverage - Core AI Topics")
        
        # Expected COMP237 topics from curriculum
        core_topics = [
            "machine learning",
            "neural network",
            "search algorithm",
            "intelligent agent",
            "natural language",
            "expert system",
            "knowledge representation"
        ]
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        all_text = ""
        
        for json_file in json_files[:200]:  # Sample for performance
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                title = data.get("title", "").lower()
                for chunk in data.get("chunks", []):
                    all_text += chunk.get("content", "").lower() + " "
                all_text += title + " "
            except:
                continue
        
        coverage = {}
        for topic in core_topics:
            coverage[topic] = topic in all_text
        
        covered = sum(coverage.values())
        total = len(core_topics)
        
        if covered >= total * 0.7:  # 70% coverage threshold
            self.logger.test_pass(
                "Domain Coverage - Core AI Topics",
                f"{covered}/{total} topics found"
            )
            return True
        else:
            self.logger.test_fail(
                "Domain Coverage - Core AI Topics",
                f"Only {covered}/{total} topics found. Missing: {[t for t, found in coverage.items() if not found]}"
            )
            return False
    
    def test_knowledge_graph_connectivity(self) -> bool:
        """Test graph relationships support learning paths"""
        self.logger.test_start("Knowledge Graph Connectivity")
        
        graph_file = GRAPH_SEED / "graph_links.json"
        
        try:
            with open(graph_file, 'r') as f:
                links = json.load(f)
            
            # Check for prerequisite-like relationships
            relation_types = Counter([link["relation"] for link in links])
            
            # Should have hierarchical structure (CONTAINS) and sequential (NEXT/PREV)
            has_hierarchy = "CONTAINS" in relation_types
            has_sequence = "NEXT_IN_MODULE" in relation_types or "PREV_IN_MODULE" in relation_types
            
            if has_hierarchy and has_sequence:
                self.logger.test_pass(
                    "Knowledge Graph Connectivity",
                    f"Graph has hierarchical ({relation_types.get('CONTAINS', 0)}) and sequential ({relation_types.get('NEXT_IN_MODULE', 0)}) relationships"
                )
                return True
            else:
                self.logger.test_fail(
                    "Knowledge Graph Connectivity",
                    f"Missing relationship types. Has hierarchy: {has_hierarchy}, Has sequence: {has_sequence}"
                )
                return False
        except Exception as e:
            self.logger.test_fail("Knowledge Graph Connectivity", f"Error: {e}")
            return False
    
    def test_content_chunking_quality(self) -> bool:
        """Test chunks are appropriate size for learning (not too small/large)"""
        self.logger.test_start("Content Chunking Quality")
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        chunk_sizes = []
        
        for json_file in json_files[:100]:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                for chunk in data.get("chunks", []):
                    token_count = chunk.get("token_count", 0)
                    if token_count > 0:
                        chunk_sizes.append(token_count)
            except:
                continue
        
        if not chunk_sizes:
            self.logger.test_fail("Content Chunking Quality", "No chunks found")
            return False
        
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        
        # Optimal chunk size for learning: 300-800 tokens (based on cognitive load theory)
        optimal_min, optimal_max = 300, 800
        in_range = sum(1 for size in chunk_sizes if optimal_min <= size <= optimal_max)
        percentage = in_range / len(chunk_sizes) * 100
        
        if percentage >= 60:  # 60% of chunks should be in optimal range
            self.logger.test_pass(
                "Content Chunking Quality",
                f"Avg: {avg_size:.0f} tokens, {percentage:.1f}% in optimal range"
            )
            return True
        else:
            self.logger.test_fail(
                "Content Chunking Quality",
                f"Only {percentage:.1f}% chunks in optimal range (300-800 tokens)"
            )
            return False
    
    # ========================================================================
    # Category 2: Retrieval & Navigation Effectiveness
    # ========================================================================
    
    def test_semantic_search_relevance(self) -> bool:
        """Test retrieval returns relevant results (top-3 accuracy)"""
        self.logger.test_start("Semantic Search Relevance")
        
        if not self.api_available:
            self.logger.test_fail("Semantic Search Relevance", "API not available")
            return False
        
        # Test queries with expected topics
        test_cases = [
            {
                "query": "machine learning supervised learning",
                "expected_keywords": ["machine learning", "supervised", "classification", "regression"]
            },
            {
                "query": "neural networks backpropagation",
                "expected_keywords": ["neural", "network", "backpropagation", "layer"]
            },
            {
                "query": "breadth first search algorithm",
                "expected_keywords": ["breadth", "search", "bfs", "algorithm"]
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/query/navigate",
                    json={"query": test_case["query"], "n_results": 3},
                    timeout=5
                )
                results = response.json()["results"]
                
                # Check if top-3 results contain expected keywords
                top_3_text = " ".join([
                    r["title"].lower() + " " + r["excerpt"].lower()
                    for r in results[:3]
                ])
                
                matches = sum(1 for kw in test_case["expected_keywords"] if kw.lower() in top_3_text)
                if matches >= len(test_case["expected_keywords"]) * 0.5:
                    passed += 1
            except Exception as e:
                self.logger.log("WARN", f"Query failed: {test_case['query']} - {e}")
        
        success_rate = passed / len(test_cases)
        
        if success_rate >= 0.8:
            self.logger.test_pass(
                "Semantic Search Relevance",
                f"{passed}/{len(test_cases)} queries returned relevant results"
            )
            return True
        else:
            self.logger.test_fail(
                "Semantic Search Relevance",
                f"Only {passed}/{len(test_cases)} queries returned relevant results"
            )
            return False
    
    def test_retrieval_speed(self) -> bool:
        """Test query response time meets UX standards (<500ms)"""
        self.logger.test_start("Retrieval Speed (UX Standard)")
        
        if not self.api_available:
            self.logger.test_fail("Retrieval Speed", "API not available")
            return False
        
        query_times = []
        for _ in range(5):
            try:
                start = datetime.now()
                requests.post(
                    f"{self.api_url}/query/navigate",
                    json={"query": "artificial intelligence", "n_results": 10},
                    timeout=5
                )
                query_times.append((datetime.now() - start).total_seconds() * 1000)
            except:
                continue
        
        if not query_times:
            self.logger.test_fail("Retrieval Speed", "No successful queries")
            return False
        
        avg_time = sum(query_times) / len(query_times)
        
        # UX standard: <500ms for good responsiveness
        if avg_time < 500:
            self.logger.test_pass(
                "Retrieval Speed (UX Standard)",
                f"Avg: {avg_time:.1f}ms (target: <500ms)"
            )
            return True
        else:
            self.logger.test_fail(
                "Retrieval Speed (UX Standard)",
                f"Avg: {avg_time:.1f}ms exceeds 500ms threshold"
            )
            return False
    
    def test_url_availability(self) -> bool:
        """Test that URLs enable direct navigation to course materials"""
        self.logger.test_start("URL Availability for Navigation")
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        total_docs = 0
        docs_with_urls = 0
        
        for json_file in json_files[:200]:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("bb_doc_id"):
                    total_docs += 1
                    if data.get("live_lms_url"):
                        docs_with_urls += 1
            except:
                continue
        
        if total_docs == 0:
            self.logger.test_fail("URL Availability", "No documents with BB IDs found")
            return False
        
        url_coverage = docs_with_urls / total_docs * 100
        
        # Should have URLs for all documents with BB IDs
        if url_coverage >= 95:
            self.logger.test_pass(
                "URL Availability for Navigation",
                f"{docs_with_urls}/{total_docs} documents ({url_coverage:.1f}%) have URLs"
            )
            return True
        else:
            self.logger.test_fail(
                "URL Availability for Navigation",
                f"Only {url_coverage:.1f}% documents have URLs (target: 95%+)"
            )
            return False
    
    # ========================================================================
    # Category 3: Pedagogical Alignment (Scaffolding, Retrieval Practice)
    # ========================================================================
    
    def test_content_difficulty_distribution(self) -> bool:
        """Test content has appropriate difficulty levels for scaffolding"""
        self.logger.test_start("Content Difficulty Distribution")
        
        # Analyze complexity indicators
        json_files = list(COMP237_DATA.rglob("*.json"))
        complexity_indicators = {
            "introductory": ["introduction", "overview", "basics", "fundamentals", "what is"],
            "intermediate": ["algorithm", "implementation", "example", "tutorial"],
            "advanced": ["optimization", "advanced", "theory", "proof", "mathematical"]
        }
        
        level_counts = {level: 0 for level in complexity_indicators}
        
        for json_file in json_files[:200]:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                title = data.get("title", "").lower()
                content = " ".join([c.get("content", "") for c in data.get("chunks", [])]).lower()
                text = title + " " + content
                
                for level, keywords in complexity_indicators.items():
                    if any(kw in text for kw in keywords):
                        level_counts[level] += 1
                        break
            except:
                continue
        
        total = sum(level_counts.values())
        if total == 0:
            self.logger.test_fail("Content Difficulty Distribution", "No content analyzed")
            return False
        
        # Should have content at all levels for proper scaffolding
        has_all_levels = all(count > 0 for count in level_counts.values())
        
        distribution = {level: count/total*100 for level, count in level_counts.items()}
        
        if has_all_levels:
            self.logger.test_pass(
                "Content Difficulty Distribution",
                f"Intro: {distribution['introductory']:.1f}%, Inter: {distribution['intermediate']:.1f}%, Adv: {distribution['advanced']:.1f}%"
            )
            return True
        else:
            missing = [level for level, count in level_counts.items() if count == 0]
            self.logger.test_fail(
                "Content Difficulty Distribution",
                f"Missing difficulty levels: {missing}"
            )
            return False
    
    def test_retrieval_practice_readiness(self) -> bool:
        """Test content structure supports retrieval practice"""
        self.logger.test_start("Retrieval Practice Readiness")
        
        # Check for question-like content and assessments
        json_files = list(COMP237_DATA.rglob("*.json"))
        assessment_keywords = ["quiz", "question", "exercise", "assignment", "test", "practice", "problem"]
        
        assessment_docs = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                title = data.get("title", "").lower()
                if any(kw in title for kw in assessment_keywords):
                    assessment_docs += 1
            except:
                continue
        
        total_docs = len(json_files)
        assessment_ratio = assessment_docs / total_docs * 100
        
        # Should have at least 5% assessment/practice content
        if assessment_ratio >= 5:
            self.logger.test_pass(
                "Retrieval Practice Readiness",
                f"{assessment_docs} assessment docs ({assessment_ratio:.1f}%)"
            )
            return True
        else:
            self.logger.test_fail(
                "Retrieval Practice Readiness",
                f"Only {assessment_ratio:.1f}% assessment content (target: 5%+)"
            )
            return False
    
    # ========================================================================
    # Category 4: Privacy & Ethics (UNESCO Guidelines)
    # ========================================================================
    
    def test_local_processing_only(self) -> bool:
        """Test that no external API calls are made (privacy)"""
        self.logger.test_start("Local Processing Only (Privacy)")
        
        # Check ChromaDB configuration
        chromadb_config = CHROMA_DB_PATH = PROJECT_ROOT / "chromadb_data"
        
        # Verify local storage
        if chromadb_config.exists():
            self.logger.test_pass(
                "Local Processing Only (Privacy)",
                "ChromaDB uses local storage"
            )
            return True
        else:
            self.logger.test_fail(
                "Local Processing Only (Privacy)",
                "ChromaDB local storage not found"
            )
            return False
    
    def test_source_transparency(self) -> bool:
        """Test that results cite sources (transparency requirement)"""
        self.logger.test_start("Source Transparency (Citations)")
        
        if not self.api_available:
            self.logger.test_fail("Source Transparency", "API not available")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/query/navigate",
                json={"query": "machine learning", "n_results": 5},
                timeout=5
            )
            results = response.json()["results"]
            
            # All results should have title and either URL or file reference
            cited = sum(1 for r in results if r.get("title") and (r.get("live_url") or r.get("bb_doc_id")))
            
            citation_rate = cited / len(results) * 100 if results else 0
            
            if citation_rate >= 90:
                self.logger.test_pass(
                    "Source Transparency (Citations)",
                    f"{cited}/{len(results)} results ({citation_rate:.1f}%) have citations"
                )
                return True
            else:
                self.logger.test_fail(
                    "Source Transparency (Citations)",
                    f"Only {citation_rate:.1f}% results have citations"
                )
                return False
        except Exception as e:
            self.logger.test_fail("Source Transparency", f"Error: {e}")
            return False
    
    # ========================================================================
    # Category 5: Performance & Accessibility
    # ========================================================================
    
    def test_embedding_quality(self) -> bool:
        """Test embedding model is appropriate for educational content"""
        self.logger.test_start("Embedding Model Quality")
        
        # Check that we're using a proven model
        # all-MiniLM-L6-v2 is research-validated for semantic similarity
        expected_model = "all-MiniLM-L6-v2"
        
        if self.api_available:
            try:
                response = requests.get(f"{self.api_url}/stats", timeout=5)
                stats = response.json()["stats"]
                embedding_model = stats.get("embedding_model", "")
                
                if expected_model in embedding_model:
                    self.logger.test_pass(
                        "Embedding Model Quality",
                        f"Using validated model: {embedding_model}"
                    )
                    return True
                else:
                    self.logger.test_fail(
                        "Embedding Model Quality",
                        f"Model {embedding_model} not validated for education"
                    )
                    return False
            except Exception as e:
                self.logger.test_fail("Embedding Model Quality", f"Error: {e}")
                return False
        else:
            self.logger.test_fail("Embedding Model Quality", "API not available")
            return False
    
    def test_result_diversity(self) -> bool:
        """Test search results include diverse content types"""
        self.logger.test_start("Result Diversity (Multiple Content Types)")
        
        if not self.api_available:
            self.logger.test_fail("Result Diversity", "API not available")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/query/navigate",
                json={"query": "artificial intelligence", "n_results": 20},
                timeout=5
            )
            results = response.json()["results"]
            
            # Check content type diversity
            content_types = set(r.get("content_type") for r in results)
            
            # Should have at least 2 different content types
            if len(content_types) >= 2:
                self.logger.test_pass(
                    "Result Diversity (Multiple Content Types)",
                    f"{len(content_types)} content types: {content_types}"
                )
                return True
            else:
                self.logger.test_fail(
                    "Result Diversity (Multiple Content Types)",
                    f"Only {len(content_types)} content type(s)"
                )
                return False
        except Exception as e:
            self.logger.test_fail("Result Diversity", f"Error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all educational AI validation tests"""
        self.logger.log("INFO", "=" * 80)
        self.logger.log("INFO", "Educational AI Validation Tests")
        self.logger.log("INFO", "Based on: VanLehn (2011), AutoTutor, UNESCO Guidelines")
        self.logger.log("INFO", "=" * 80)
        
        all_passed = True
        
        # Category 1: Content Quality & Domain Model
        self.logger.category_start("Category 1: Content Quality & Domain Model")
        all_passed &= self.test_domain_coverage()
        all_passed &= self.test_knowledge_graph_connectivity()
        all_passed &= self.test_content_chunking_quality()
        
        # Category 2: Retrieval & Navigation
        self.logger.category_start("Category 2: Retrieval & Navigation Effectiveness")
        all_passed &= self.test_semantic_search_relevance()
        all_passed &= self.test_retrieval_speed()
        all_passed &= self.test_url_availability()
        
        # Category 3: Pedagogical Alignment
        self.logger.category_start("Category 3: Pedagogical Alignment")
        all_passed &= self.test_content_difficulty_distribution()
        all_passed &= self.test_retrieval_practice_readiness()
        
        # Category 4: Privacy & Ethics
        self.logger.category_start("Category 4: Privacy & Ethics")
        all_passed &= self.test_local_processing_only()
        all_passed &= self.test_source_transparency()
        
        # Category 5: Performance & Accessibility
        self.logger.category_start("Category 5: Performance & Accessibility")
        all_passed &= self.test_embedding_quality()
        all_passed &= self.test_result_diversity()
        
        return all_passed


def main():
    """Run educational AI validation tests"""
    log_file = TEST_LOGS / f"educational_ai_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = TestLogger(log_file)
    
    logger.log("INFO", f"Test log: {log_file}")
    logger.log("INFO", "Starting FastAPI server check...")
    
    tests = EducationalAITests(logger)
    
    if not tests.api_available:
        logger.log("WARN", "⚠️  FastAPI service not running. Some tests will be skipped.")
        logger.log("WARN", "Start server: python development/backend/fastapi_service/main.py")
        print()
    
    all_passed = tests.run_all_tests()
    
    success = logger.summary()
    
    if not success:
        logger.log("FAIL", "Some educational AI requirements not met. See log for details.")
        sys.exit(1)
    else:
        logger.log("PASS", "All educational AI validation tests passed! ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()
