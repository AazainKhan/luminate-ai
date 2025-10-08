"""
Integration Test Suite for Luminate AI Data Pipeline
Purpose: Catch regressions and validate data processing before moving to next phase

Tests:
1. Data ingestion integrity
2. URL mapping correctness
3. Graph relationship validation
4. Chunk quality checks
5. File processing coverage
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import re

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up to actual project root
COMP237_DATA = PROJECT_ROOT / "comp_237_content"
GRAPH_SEED = PROJECT_ROOT / "graph_seed"
LOGS_DIR = PROJECT_ROOT / "logs"
TEST_LOGS = PROJECT_ROOT / "development/tests/logs"

# Create test logs directory
TEST_LOGS.mkdir(parents=True, exist_ok=True)


class TestLogger:
    """Simple test logger with color output"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
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
                "END": "\033[0m"      # Reset
            }
            color = colors.get(level, "")
            print(f"{color}[{level}]{colors['END']} {message}")
    
    def test_start(self, test_name: str):
        self.tests_run += 1
        self.log("INFO", f"Running test: {test_name}")
    
    def test_pass(self, test_name: str, details: str = ""):
        self.tests_passed += 1
        msg = f"✓ {test_name}"
        if details:
            msg += f" - {details}"
        self.log("PASS", msg)
    
    def test_fail(self, test_name: str, reason: str):
        self.tests_failed += 1
        self.log("FAIL", f"✗ {test_name} - {reason}")
    
    def summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        self.log("INFO", "=" * 80)
        self.log("INFO", f"Test Summary")
        self.log("INFO", f"Total: {self.tests_run}, Passed: {self.tests_passed}, Failed: {self.tests_failed}")
        self.log("INFO", f"Duration: {duration:.2f}s")
        self.log("INFO", "=" * 80)
        return self.tests_failed == 0


class LuminateIntegrationTests:
    """Integration tests for data pipeline"""
    
    def __init__(self, logger: TestLogger):
        self.logger = logger
        self.course_id = "_11378_1"
        self.expected_total_files = 909
        
    def test_data_directory_exists(self) -> bool:
        """Test that processed data directory exists"""
        self.logger.test_start("Data Directory Exists")
        
        if not COMP237_DATA.exists():
            self.logger.test_fail("Data Directory Exists", f"Missing: {COMP237_DATA}")
            return False
        
        self.logger.test_pass("Data Directory Exists", f"Found: {COMP237_DATA}")
        return True
    
    def test_json_files_count(self) -> bool:
        """Test expected number of JSON files"""
        self.logger.test_start("JSON Files Count")
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        count = len(json_files)
        
        # We expect 593 JSON files based on processing summary
        expected = 593
        if count != expected:
            self.logger.test_fail(
                "JSON Files Count", 
                f"Expected {expected}, found {count}"
            )
            return False
        
        self.logger.test_pass("JSON Files Count", f"{count} files found")
        return True
    
    def test_course_id_correctness(self) -> bool:
        """Test that all URLs use correct COMP237 course ID"""
        self.logger.test_start("Course ID Correctness")
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        incorrect_urls = []
        
        for json_file in json_files[:50]:  # Sample first 50
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Check course_id field
                if data.get("course_id") != self.course_id:
                    incorrect_urls.append(
                        (json_file.name, "course_id", data.get("course_id"))
                    )
                
                # Check URL contains correct course ID
                url = data.get("live_lms_url")
                if url and self.course_id not in url:
                    incorrect_urls.append((json_file.name, "url", url))
                    
            except Exception as e:
                self.logger.test_fail(
                    "Course ID Correctness",
                    f"Error reading {json_file.name}: {e}"
                )
                return False
        
        if incorrect_urls:
            self.logger.test_fail(
                "Course ID Correctness",
                f"Found {len(incorrect_urls)} files with incorrect IDs"
            )
            for fname, field, value in incorrect_urls[:5]:
                self.logger.log("WARN", f"  {fname}: {field} = {value}")
            return False
        
        self.logger.test_pass("Course ID Correctness", "All sampled files correct")
        return True
    
    def test_url_format_validation(self) -> bool:
        """Test URL format matches Blackboard Ultra pattern"""
        self.logger.test_start("URL Format Validation")
        
        # Expected pattern
        url_pattern = re.compile(
            r'^https://luminate\.centennialcollege\.ca/ultra/courses/'
            r'_\d+_1/outline/edit/document/_\d+_1\?'
            r'courseId=_\d+_1&view=content&state=view$'
        )
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        invalid_urls = []
        
        for json_file in json_files[:100]:  # Sample 100 files
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                url = data.get("live_lms_url")
                if url and not url_pattern.match(url):
                    invalid_urls.append((json_file.name, url))
                    
            except Exception as e:
                self.logger.log("WARN", f"Error reading {json_file.name}: {e}")
        
        if invalid_urls:
            self.logger.test_fail(
                "URL Format Validation",
                f"Found {len(invalid_urls)} invalid URLs"
            )
            for fname, url in invalid_urls[:3]:
                self.logger.log("WARN", f"  {fname}: {url}")
            return False
        
        self.logger.test_pass("URL Format Validation", "All sampled URLs valid")
        return True
    
    def test_chunk_structure(self) -> bool:
        """Test that chunks have required fields and valid data"""
        self.logger.test_start("Chunk Structure Validation")
        
        required_chunk_fields = [
            "chunk_id", "content", "tags", "live_lms_url",
            "token_count", "chunk_index", "total_chunks"
        ]
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        issues = []
        
        for json_file in json_files[:50]:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                chunks = data.get("chunks", [])
                if not chunks:
                    continue
                
                for i, chunk in enumerate(chunks):
                    # Check required fields
                    missing = [f for f in required_chunk_fields if f not in chunk]
                    if missing:
                        issues.append(
                            f"{json_file.name} chunk {i}: missing {missing}"
                        )
                    
                    # Validate token count is reasonable
                    if chunk.get("token_count", 0) == 0:
                        issues.append(
                            f"{json_file.name} chunk {i}: zero token count"
                        )
                    
                    # Validate chunk index
                    if chunk.get("chunk_index") != i:
                        issues.append(
                            f"{json_file.name} chunk {i}: index mismatch"
                        )
                        
            except Exception as e:
                issues.append(f"{json_file.name}: {e}")
        
        if issues:
            self.logger.test_fail(
                "Chunk Structure Validation",
                f"Found {len(issues)} issues"
            )
            for issue in issues[:5]:
                self.logger.log("WARN", f"  {issue}")
            return False
        
        self.logger.test_pass("Chunk Structure Validation", "All chunks valid")
        return True
    
    def test_graph_relationships(self) -> bool:
        """Test graph links file exists and has correct structure"""
        self.logger.test_start("Graph Relationships")
        
        graph_file = GRAPH_SEED / "graph_links.json"
        
        if not graph_file.exists():
            self.logger.test_fail("Graph Relationships", f"Missing: {graph_file}")
            return False
        
        try:
            with open(graph_file, 'r') as f:
                links = json.load(f)
            
            # Expected ~1,296 relationships
            if not isinstance(links, list):
                self.logger.test_fail(
                    "Graph Relationships",
                    "graph_links.json is not a list"
                )
                return False
            
            expected_count = 1296
            actual_count = len(links)
            
            # Allow 5% variance
            if abs(actual_count - expected_count) > expected_count * 0.05:
                self.logger.test_fail(
                    "Graph Relationships",
                    f"Expected ~{expected_count}, found {actual_count}"
                )
                return False
            
            # Validate structure of first few links
            required_fields = ["source", "target", "relation"]
            for i, link in enumerate(links[:10]):
                missing = [f for f in required_fields if f not in link]
                if missing:
                    self.logger.test_fail(
                        "Graph Relationships",
                        f"Link {i} missing fields: {missing}"
                    )
                    return False
            
            self.logger.test_pass(
                "Graph Relationships",
                f"{actual_count} links with valid structure"
            )
            return True
            
        except Exception as e:
            self.logger.test_fail("Graph Relationships", f"Error: {e}")
            return False
    
    def test_metadata_completeness(self) -> bool:
        """Test that metadata fields are populated correctly"""
        self.logger.test_start("Metadata Completeness")
        
        required_fields = [
            "course_id", "course_name", "module", "file_name",
            "content_type", "bb_doc_id", "title"
        ]
        
        json_files = list(COMP237_DATA.rglob("*.json"))
        incomplete = []
        
        for json_file in json_files[:100]:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Check if document has BB ID (should have URL)
                has_bb_id = data.get("bb_doc_id") is not None
                has_url = data.get("live_lms_url") is not None
                
                if has_bb_id and not has_url:
                    incomplete.append(
                        f"{json_file.name}: has BB ID but no URL"
                    )
                
                # Check basic metadata
                if data.get("course_id") != self.course_id:
                    incomplete.append(
                        f"{json_file.name}: wrong course_id"
                    )
                
                if data.get("course_name") != "COMP237":
                    incomplete.append(
                        f"{json_file.name}: wrong course_name"
                    )
                    
            except Exception as e:
                incomplete.append(f"{json_file.name}: {e}")
        
        if incomplete:
            self.logger.test_fail(
                "Metadata Completeness",
                f"Found {len(incomplete)} issues"
            )
            for issue in incomplete[:5]:
                self.logger.log("WARN", f"  {issue}")
            return False
        
        self.logger.test_pass("Metadata Completeness", "All metadata valid")
        return True
    
    def test_summary_file(self) -> bool:
        """Test that ingest_summary.json exists and is accurate"""
        self.logger.test_start("Summary File Validation")
        
        summary_file = PROJECT_ROOT / "ingest_summary.json"
        
        if not summary_file.exists():
            self.logger.test_fail("Summary File Validation", "Missing summary file")
            return False
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            # Validate key metrics (actual structure has nested dicts)
            pipeline_info = summary.get("pipeline_info", {})
            statistics = summary.get("statistics", {})
            
            validations = [
                (statistics.get("total_files"), 909, "total_files"),
                (statistics.get("processed_files"), 593, "processed_files"),
                (statistics.get("total_chunks"), 917, "total_chunks"),
                (pipeline_info.get("course_id"), self.course_id, "course_id")
            ]
            
            for actual_val, expected_val, key in validations:
                if actual_val != expected_val:
                    self.logger.test_fail(
                        "Summary File Validation",
                        f"{key}: expected {expected_val}, got {actual_val}"
                    )
                    return False
            
            self.logger.test_pass("Summary File Validation", "Summary accurate")
            return True
            
        except Exception as e:
            self.logger.test_fail("Summary File Validation", f"Error: {e}")
            return False
    
    def test_log_files_exist(self) -> bool:
        """Test that processing logs were created"""
        self.logger.test_start("Log Files Exist")
        
        expected_logs = [
            LOGS_DIR / "ingestion.log",
            LOGS_DIR / "ingest_issues.txt"
        ]
        
        missing = [log for log in expected_logs if not log.exists()]
        
        if missing:
            self.logger.test_fail(
                "Log Files Exist",
                f"Missing: {[str(l) for l in missing]}"
            )
            return False
        
        self.logger.test_pass("Log Files Exist", "All logs present")
        return True
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        self.logger.log("INFO", "=" * 80)
        self.logger.log("INFO", "Starting Luminate AI Integration Tests")
        self.logger.log("INFO", f"Course ID: {self.course_id}")
        self.logger.log("INFO", "=" * 80)
        
        tests = [
            self.test_data_directory_exists,
            self.test_json_files_count,
            self.test_course_id_correctness,
            self.test_url_format_validation,
            self.test_chunk_structure,
            self.test_graph_relationships,
            self.test_metadata_completeness,
            self.test_summary_file,
            self.test_log_files_exist
        ]
        
        all_passed = True
        for test in tests:
            try:
                if not test():
                    all_passed = False
            except Exception as e:
                self.logger.test_fail(test.__name__, f"Exception: {e}")
                all_passed = False
        
        return all_passed


def main():
    """Run integration tests and report results"""
    log_file = TEST_LOGS / f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = TestLogger(log_file)
    
    logger.log("INFO", f"Test log: {log_file}")
    
    tests = LuminateIntegrationTests(logger)
    all_passed = tests.run_all_tests()
    
    success = logger.summary()
    
    if not success:
        logger.log("FAIL", "Some tests failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.log("PASS", "All integration tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
