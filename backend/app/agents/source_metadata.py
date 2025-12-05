"""
Standardized Source Metadata Handling

This module provides consistent extraction and formatting of source metadata
from RAG retrieval results. Fixes the "Unknown" sources bug by handling
various metadata formats that can occur in the pipeline.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Standardized source metadata."""
    filename: str
    chunk_index: int
    relevance_score: float
    content_preview: str
    content_type: Optional[str] = None
    page_number: Optional[int] = None
    url: Optional[str] = None
    bb_content_id: Optional[str] = None
    bb_course_id: Optional[str] = None
    
    def _get_display_title(self) -> str:
        """
        Generate a user-friendly display title from the filename.
        Extracts week/lecture/lab info and topic names.
        """
        import re
        
        filename = self.filename
        if not filename or filename == "Unknown":
            return "Course Material"
        
        # Remove extension
        base_name = re.sub(r'\.[^/.]+$', '', filename)
        lower_name = base_name.lower()
        
        # Handle res##### format - extract topic from content if possible
        if re.match(r'^res\d+$', base_name, re.IGNORECASE):
            content = self.content_preview.lower() if self.content_preview else ""
            
            # ML/AI topic detection
            topic_patterns = [
                (r'neural network|hidden layer|perceptron|feedforward|feed.?forward', 'Neural Networks'),
                (r'gradient descent|learning rate', 'Gradient Descent'),
                (r'backpropagation|back.?prop', 'Backpropagation'),
                (r'decision tree', 'Decision Trees'),
                (r'support vector|svm', 'Support Vector Machines'),
                (r'k-?nearest|knn', 'K-Nearest Neighbors'),
                (r'naive bayes', 'Naive Bayes'),
                (r'regression|linear model', 'Regression'),
                (r'classification|classifier', 'Classification'),
                (r'clustering|k-?means', 'Clustering'),
                (r'overfitting|underfitting', 'Model Fitting'),
                (r'cross.?validation', 'Cross Validation'),
                (r'activation function', 'Activation Functions'),
                (r'loss function|cost function', 'Loss Functions'),
                (r'layer|input layer|output layer', 'Network Layers'),
                (r'epoch|batch|training', 'Model Training'),
                (r'accuracy|precision|recall|f1', 'Model Evaluation'),
            ]
            
            for pattern, topic in topic_patterns:
                if re.search(pattern, content):
                    return topic
            
            return "Course Material"
        
        # Handle syllabus
        if 'syllabus' in lower_name:
            section_match = re.search(r'section[_\-\s]?(\d+)', lower_name)
            if section_match:
                return f"Syllabus - Section {section_match.group(1)}"
            if 'map' in lower_name:
                return "Course Structure"
            return "Course Syllabus"
        
        # Extract structural info
        parts = []
        week_match = re.search(r'week[_\-\s]?(\d+)', lower_name)
        lecture_match = re.search(r'lecture[_\-\s]?(\d+)', lower_name)
        lab_match = re.search(r'lab[_\-\s]?(\d+)', lower_name)
        assignment_match = re.search(r'(?:assignment|hw|homework)[_\-\s]?(\d+)', lower_name)
        
        if week_match:
            parts.append(f"Week {week_match.group(1)}")
        if lecture_match:
            parts.append(f"Lecture {lecture_match.group(1)}")
        if lab_match:
            parts.append(f"Lab {lab_match.group(1)}")
        if assignment_match:
            parts.append(f"Assignment {assignment_match.group(1)}")
        
        if parts:
            # Try to extract remaining topic
            clean_name = re.sub(r'week[_\-\s]?\d+', '', base_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'lecture[_\-\s]?\d+', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'lab[_\-\s]?\d+', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'(?:assignment|hw|homework)[_\-\s]?\d+', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'[_\-]+', ' ', clean_name).strip()
            
            if len(clean_name) > 2:
                topic = ' '.join(w.capitalize() for w in clean_name.split())
                parts.append(f"- {topic}")
            
            return ' '.join(parts)
        
        # Default: clean up filename
        return ' '.join(w.capitalize() for w in re.sub(r'[_\-]+', ' ', base_name).split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        display_title = self._get_display_title()
        
        # Add page number to description if available
        page_info = f" (Page {self.page_number})" if self.page_number else ""
        
        return {
            "title": display_title + page_info,
            "url": self.url or "",
            "description": f"{self.content_preview[:150]}..." if self.content_preview else f"Relevance: {self.relevance_score:.0%}",
            "filename": self.filename,
            "source_file": self.filename,  # Add for frontend compatibility
            "chunk_index": self.chunk_index,
            "relevance_score": self.relevance_score,
            "content_type": self.content_type,
            "page_number": self.page_number,
            "page": self.page_number,  # Add for frontend compatibility
            "bb_content_id": self.bb_content_id,
            "bb_course_id": self.bb_course_id
        }
    
    def to_citation(self) -> str:
        """Format for inline citation with context."""
        display_title = self._get_display_title()
        
        if self.url:
            return f"[{display_title}]({self.url})"
        if self.page_number:
            return f"[{display_title}, p.{self.page_number}]"
        return f"[{display_title}]"
    
    @classmethod
    def from_rag_result(cls, result: Dict[str, Any]) -> "Source":
        """
        Create Source from RAG retrieval result.
        
        Handles multiple metadata formats:
        - Flat structure: {"source_filename": "...", "content": "..."}
        - Nested metadata: {"metadata": {"source_file": "..."}, "text": "..."}
        - LangChain Document: {"page_content": "...", "metadata": {...}}
        """
        # Extract metadata dict (handle both dict and object with metadata attr)
        if isinstance(result, dict):
            metadata = result.get("metadata", {}) or {}
        else:
            metadata = getattr(result, "metadata", {}) or {}
        
        # Extract filename from various possible keys (order matters!)
        filename = None
        
        # Try flat structure first
        if isinstance(result, dict):
            filename = (
                result.get("source_filename") or
                result.get("source_file") or
                result.get("filename") or
                result.get("source") or
                result.get("title") # Fallback to title if filename missing
            )
        
        # Try nested metadata
        if not filename and metadata:
            filename = (
                metadata.get("source_filename") or
                metadata.get("source_file") or
                metadata.get("source") or
                metadata.get("filename") or
                metadata.get("title")
            )
        
        # Default to Unknown
        if not filename:
            filename = "Unknown"
        
        # Clean up filename
        if filename and filename != "Unknown":
            # Remove path prefix if present
            if "/" in filename:
                filename = filename.split("/")[-1]
            if "\\" in filename:
                filename = filename.split("\\")[-1]
        
        # Extract chunk index
        chunk_index = (
            result.get("chunk_index") or
            result.get("metadata", {}).get("chunk_index") or
            result.get("chunk_id") or
            result.get("metadata", {}).get("chunk_id") or
            0
        )
        if isinstance(chunk_index, str):
            try:
                chunk_index = int(chunk_index)
            except ValueError:
                chunk_index = 0
        
        # Extract relevance score
        relevance_score = (
            result.get("relevance_score") or
            result.get("score") or
            result.get("distance") or
            result.get("similarity") or
            0.0
        )
        # If it's a distance (higher = farther), convert to similarity
        if isinstance(relevance_score, (int, float)) and relevance_score > 1.0:
            relevance_score = max(0.0, 1.0 - min(relevance_score, 2.0) / 2.0)
        
        # Extract content - note: careful with operator precedence!
        content = (
            result.get("content") or
            result.get("text") or
            result.get("page_content") or
            (getattr(result, "page_content", "") if hasattr(result, "page_content") else "") or
            ""
        )
        
        # Extract optional fields
        content_type = (
            result.get("content_type") or
            result.get("metadata", {}).get("content_type") or
            result.get("type")
        )
        
        page_number = (
            result.get("page_number") or
            result.get("page") or
            result.get("metadata", {}).get("page_number") or
            result.get("metadata", {}).get("page")
        )
        if page_number:
            try:
                page_number = int(page_number)
            except (ValueError, TypeError):
                page_number = None
        
        # Extract Blackboard IDs
        bb_content_id = (
            result.get("bb_content_id") or
            metadata.get("bb_content_id")
        )
        bb_course_id = (
            result.get("bb_course_id") or
            metadata.get("bb_course_id")
        )
        
        url = (
            result.get("public_url") or
            result.get("url") or
            result.get("metadata", {}).get("public_url") or
            result.get("metadata", {}).get("url")
        )
        
        # Construct Deep Link if IDs are present
        if bb_content_id and bb_course_id:
            # Format: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_3960966_1?courseId=_29430_1&view=content&state=view
            url = f"https://luminate.centennialcollege.ca/ultra/courses/{bb_course_id}/outline/edit/document/{bb_content_id}?courseId={bb_course_id}&view=content&state=view"
        
        return cls(
            filename=filename,
            chunk_index=chunk_index,
            relevance_score=float(relevance_score) if relevance_score else 0.0,
            content_preview=content[:200] if content else "",
            content_type=content_type,
            page_number=page_number,
            url=url,
            bb_content_id=bb_content_id,
            bb_course_id=bb_course_id
        )


def extract_sources(rag_results: List[Any]) -> List[Source]:
    """
    Extract and deduplicate sources from RAG results.
    
    Args:
        rag_results: List of RAG retrieval results (dicts or Documents)
        
    Returns:
        List of Source objects, deduplicated and sorted by relevance
    """
    if not rag_results:
        return []
    
    sources = []
    seen_files = set()
    
    for result in rag_results:
        try:
            # Handle LangChain Document objects
            if hasattr(result, "page_content"):
                result_dict = {
                    "content": result.page_content,
                    "metadata": result.metadata if hasattr(result, "metadata") else {}
                }
                source = Source.from_rag_result(result_dict)
            else:
                source = Source.from_rag_result(result)
            
            # Skip duplicates from same file (keep highest relevance)
            file_key = f"{source.filename}_{source.chunk_index}"
            if file_key in seen_files:
                continue
            seen_files.add(file_key)
            
            sources.append(source)
            
        except Exception as e:
            logger.warning(f"Failed to extract source from result: {e}")
            continue
    
    # Sort by relevance (highest first)
    sources.sort(key=lambda s: s.relevance_score, reverse=True)
    
    # Log extraction results
    valid_sources = [s for s in sources if s.filename != "Unknown"]
    logger.info(f"📚 Extracted {len(valid_sources)} valid sources from {len(rag_results)} results")
    
    return sources


def format_sources_for_response(sources: List[Source], max_sources: int = 3) -> str:
    """
    Format sources for appending to response.
    
    Args:
        sources: List of Source objects
        max_sources: Maximum number of sources to include
        
    Returns:
        Formatted string to append to response, or empty string if no valid sources
    """
    if not sources:
        return ""
    
    # Filter out unknown sources
    valid_sources = [s for s in sources if s.filename != "Unknown"][:max_sources]
    
    if not valid_sources:
        return ""
    
    citations = [s.to_citation() for s in valid_sources]
    return f"\n\n**Sources:** {', '.join(citations)}"


def format_sources_for_context(sources: List[Source], max_sources: int = 5) -> str:
    """
    Format sources for including in LLM context.
    
    Args:
        sources: List of Source objects
        max_sources: Maximum number of sources to include
        
    Returns:
        Formatted string for LLM context
    """
    if not sources:
        return "No course materials retrieved for this query."
    
    valid_sources = [s for s in sources if s.filename != "Unknown"][:max_sources]
    
    if not valid_sources:
        return "No course materials retrieved for this query."
    
    parts = []
    for i, source in enumerate(valid_sources, 1):
        parts.append(f"[Source {i}: {source.filename}] (relevance: {source.relevance_score:.2f})")
        if source.content_preview:
            parts.append(source.content_preview)
        parts.append("---")
    
    return "\n".join(parts)


def normalize_rag_results(results: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalize RAG results to consistent format for downstream processing.
    
    This ensures all results have the same structure regardless of
    whether they came from LangChain, direct ChromaDB, or other sources.
    """
    normalized = []
    
    for result in results:
        source = Source.from_rag_result(result if isinstance(result, dict) else {"content": str(result)})
        
        # Get original content
        if hasattr(result, "page_content"):
            content = result.page_content
        elif isinstance(result, dict):
            content = result.get("content") or result.get("text") or result.get("page_content", "")
        else:
            content = str(result)
        
        normalized.append({
            "content": content,
            "source_filename": source.filename,
            "chunk_index": source.chunk_index,
            "relevance_score": source.relevance_score,
            "content_type": source.content_type,
            "page_number": source.page_number,
            "url": source.url,
        })
    
    return normalized
