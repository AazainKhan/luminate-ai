"""
Direct RAG Tool - Uses Docker ChromaDB (memory_store) directly

No LangChain wrappers - simpler, faster, fewer dependencies.
Based on Adarsh's DirectRAGRetriever pattern.

Uses Gemini embeddings (768-dim) to match the ingested documents.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
import chromadb
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings as app_settings
from app.agent.schemas import Source, RAGMetadata

logger = logging.getLogger(__name__)


# OER is now ALWAYS retrieved as optional supplementary source
# The LLM decides which sources to actually cite based on relevance


class RAGRetriever:
    """
    Multi-collection ChromaDB retriever for COMP237.
    
    Collections:
    1. comp237_course_materials (403 docs) - Primary course content
    2. oer_resources (73 docs) - MIT Math for ML supplementary materials
    3. embedded_resources (247 docs) - Mediasite videos, URLs, external links
    
    All collections are always queried. The LLM decides which sources
    to cite based on relevance via citation confidence scoring.
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = "comp237_course_materials",  # Primary collection
        oer_collection_name: str = "oer_resources",  # Supplementary OER collection
        embedded_collection_name: str = "embedded_resources",  # Mediasite/URLs collection
    ):
        """
        Initialize multi-collection RAG retriever.
        
        Args:
            host: ChromaDB host (defaults to Docker service 'memory_store')
            port: ChromaDB port (defaults to 8000 internal Docker port)
            collection_name: Primary course collection
            oer_collection_name: OER supplementary collection (MIT Math for ML)
            embedded_collection_name: Embedded resources (mediasite, URLs)
        """
        self.host = host or app_settings.chromadb_host
        self.port = port or app_settings.chromadb_port
        self.collection_name = collection_name
        self.oer_collection_name = oer_collection_name
        self.embedded_collection_name = embedded_collection_name
        self.client = None
        self._embeddings = None
        self._connect()
        self._init_embeddings()
    
    def _connect(self):
        """Establish connection to ChromaDB Docker service"""
        try:
            # Connect to Docker ChromaDB service
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(anonymized_telemetry=False)
            )
            # Test connection
            heartbeat = self.client.heartbeat()
            logger.info(f"✅ Connected to ChromaDB at {self.host}:{self.port} (heartbeat: {heartbeat})")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB at {self.host}:{self.port}: {e}")
            raise ConnectionError(f"ChromaDB not available at {self.host}:{self.port}. Is Docker running?")
    
    def _init_embeddings(self):
        """Initialize Gemini embeddings (768-dim) to match ingested documents"""
        try:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=app_settings.google_api_key
            )
            logger.info("✅ Initialized Gemini embeddings (768-dim)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini embeddings: {e}")
            raise ValueError("Gemini API key not configured. Set GOOGLE_API_KEY.")
    
    def _get_collection(self, collection_name: str = None, quiet: bool = False):
        """Get a specific collection by name"""
        name = collection_name or self.collection_name
        try:
            return self.client.get_collection(name)
        except Exception as e:
            if not quiet:
                logger.warning(f"Collection {name} not found: {e}")
            # List available collections
            collections = self.client.list_collections()
            names = [c.name for c in collections]
            if not quiet:
                logger.info(f"Available collections: {names}")
            
            # Try common alternatives for course collection
            if not collection_name:
                for alt_name in ["comp237_course_materials", "course_comp237", "COMP237"]:
                    try:
                        return self.client.get_collection(alt_name)
                    except:
                        continue
            
            raise ValueError(f"Collection {name} not found. Available: {names}")
    
    def _get_oer_collection(self):
        """Get OER supplementary collection (returns None if not available)"""
        try:
            return self._get_collection(self.oer_collection_name, quiet=True)
        except ValueError:
            logger.debug(f"OER collection '{self.oer_collection_name}' not available - skipping OER search")
            return None
    
    def _get_embedded_collection(self):
        """Get embedded resources collection (returns None if not available)"""
        try:
            return self._get_collection(self.embedded_collection_name, quiet=True)
        except ValueError:
            logger.info(f"Embedded resources collection '{self.embedded_collection_name}' not available - skipping embedded resources")
            return None
    
    def retrieve(
        self,
        query: str,
        k: int = 5,  # Increased from 3 to accommodate 3 collections
        threshold: float = 0.30,  # Lowered from 0.35 to 0.30 - scores typically ~0.34
    ) -> Tuple[List[Dict[str, Any]], RAGMetadata]:
        """
        Retrieve relevant documents from all ChromaDB collections.
        
        Strategy:
        1. Always query ALL collections:
           - comp237_course_materials (primary, highest priority)
           - oer_resources (supplementary math/ML theory)
           - embedded_resources (mediasite videos, URLs)
        2. Merge and rank results by relevance + source type
        3. Add citation_confidence score for each source
        4. LLM decides which sources to cite inline based on confidence
        
        Args:
            query: The search query
            k: Number of results to return (default 5 to accommodate 3 collections)
            threshold: Minimum similarity score (0-1)
            
        Returns:
            Tuple of (documents list with citation_confidence, RAG metadata)
        """
        docs: List[Dict[str, Any]] = []
        
        # Blacklist for irrelevant administrative documents
        BLACKLIST_TITLES = [
            "Copyright Permissions",
            "Table of Contents",
            "Index",
            "Glossary",
            "References",
            "Bibliography"
        ]
        
        try:
            # Generate query embedding once (used for both collections)
            query_embedding = self._embeddings.embed_query(query)
            
            # --- COURSE COLLECTION (Primary) ---
            collection = self._get_collection()
            course_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=int(k * 1.5),  # Fetch more to allow for filtering, but leave room for OER
                include=["documents", "metadatas", "distances"],
            )
            
            # --- OER COLLECTION (Always query as supplementary) ---
            logger.info("Querying OER collection (MIT Math for ML) for supplementary theory...")
            oer_collection = self._get_oer_collection()
            oer_results = None
            if oer_collection:
                try:
                    oer_results = oer_collection.query(
                        query_embeddings=[query_embedding],
                        n_results=max(2, k - 1),  # Fetch fewer OER docs to prioritize course content
                        include=["documents", "metadatas", "distances"],
                    )
                    logger.info(f"OER: Found {len(oer_results.get('documents', [[]])[0])} supplementary docs")
                except Exception as e:
                    logger.warning(f"OER search failed: {e}")
            
            # --- EMBEDDED RESOURCES COLLECTION (Always query for mediasite/URLs) ---
            logger.info("Querying embedded resources (mediasite links, URLs)...")
            embedded_collection = self._get_embedded_collection()
            embedded_results = None
            if embedded_collection:
                try:
                    embedded_results = embedded_collection.query(
                        query_embeddings=[query_embedding],
                        n_results=k,
                        include=["documents", "metadatas", "distances"],
                    )
                    logger.info(f"Embedded: Found {len(embedded_results.get('documents', [[]])[0])} media/URL resources")
                except Exception as e:
                    logger.warning(f"Embedded resources search failed: {e}")            # --- PROCESS COURSE RESULTS (Primary) ---
            course_docs = []
            docs_raw = course_results.get("documents", [[]])[0]
            metas_raw = course_results.get("metadatas", [[]])[0]
            dists_raw = course_results.get("distances", [[]])[0]
            
            for doc, meta, dist in zip(docs_raw, metas_raw, dists_raw):
                # Convert distance to similarity score (higher = more similar)
                score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
                
                if score >= threshold:
                    meta = meta or {}
                    source = meta.get("title") or meta.get("resource_id") or "Unknown"
                    
                    # Filter out blacklisted titles
                    if any(blocked.lower() in source.lower() for blocked in BLACKLIST_TITLES):
                        continue
                        
                    # Filter out very short content (likely noise/headers)
                    if len(doc) < 50:
                        continue

                    module = meta.get("module", "")
                    week = meta.get("week", "")
                    
                    # Extract URLs from enriched metadata
                    primary_url = meta.get("primary_url", "")
                    primary_url_type = meta.get("primary_url_type", "")
                    has_urls = meta.get("has_urls", False)
                    
                    # Parse additional URLs if available
                    import json
                    all_urls = []
                    url_types = []
                    try:
                        if meta.get("urls"):
                            all_urls = json.loads(meta["urls"])
                        if meta.get("url_types"):
                            url_types = json.loads(meta["url_types"])
                    except:
                        pass
                    
                    # Citation confidence: High for course content if score > 0.4 (likely to be cited inline)
                    citation_confidence = "high" if score > 0.4 else "medium"
                    
                    # Map URL type to link_type (for consistency with embedded resources)
                    link_type = None
                    if primary_url_type:
                        if primary_url_type == "blackboard":
                            link_type = "blackboard"  # Blackboard course content (highest priority)
                        elif primary_url_type == "mediasite_video":
                            link_type = "mediasite"
                        elif primary_url_type in ["wikipedia", "external", "youtube", "pdf", "code"]:
                            link_type = "generic_url"
                    
                    course_docs.append({
                        "content": doc,
                        "metadata": meta,
                        "score": score,
                        "source_file": f"{module} - {source}" if module else source,
                        "title": source,
                        "module": module,
                        "week": week,
                        "source_type": "course",
                        "citation_confidence": citation_confidence,
                        "url": primary_url if has_urls else None,
                        "link_type": link_type,
                        "all_urls": all_urls if all_urls else None,
                        "url_types": url_types if url_types else None,
                    })
            
            # --- PROCESS OER RESULTS (Supplementary) ---
            oer_docs = []
            if oer_results:
                oer_docs_raw = oer_results.get("documents", [[]])[0]
                oer_metas_raw = oer_results.get("metadatas", [[]])[0]
                oer_dists_raw = oer_results.get("distances", [[]])[0]
                
                for doc, meta, dist in zip(oer_docs_raw, oer_metas_raw, oer_dists_raw):
                    score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
                    
                    # Lower threshold for OER (more lenient)
                    if score >= threshold * 0.8:  # 80% of course threshold
                        meta = meta or {}
                        
                        # Filter out short content
                        if len(doc) < 50:
                            continue
                        
                        # Build OER source identifier
                        topic = meta.get("topic", "")
                        subtopic = meta.get("subtopic", "")
                        source_title = meta.get("source_title", "OER Resource")
                        section = meta.get("section_heading", meta.get("title", ""))
                        
                        title = f"{topic} - {section}" if topic and section else (section or topic or "OER Resource")
                        source_file = f"{source_title}: {title}"
                        
                        # Citation confidence: Medium for OER (background theory, less likely to be cited inline)
                        citation_confidence = "medium" if score > 0.35 else "low"
                        
                        oer_docs.append({
                            "content": doc,
                            "metadata": meta,
                            "score": score * 0.85,  # Lower priority than course content
                            "source_file": source_file,
                            "title": title,
                            "module": source_title,
                            "week": "",
                            "source_type": "oer",
                            "citation_confidence": citation_confidence,
                            "oer_topic": topic,
                            "oer_source": source_title,
                        })
            
            # --- PROCESS EMBEDDED RESOURCES (Mediasite/URLs) ---
            embedded_docs = []
            if embedded_results:
                embedded_docs_raw = embedded_results.get("documents", [[]])[0]
                embedded_metas_raw = embedded_results.get("metadatas", [[]])[0]
                embedded_dists_raw = embedded_results.get("distances", [[]])[0]
                
                for doc, meta, dist in zip(embedded_docs_raw, embedded_metas_raw, embedded_dists_raw):
                    score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
                    
                    if score >= threshold * 0.8 and len(doc) >= 50:
                        meta = meta or {}
                        
                        link_type = meta.get("link_type", "url")
                        url = meta.get("url", "")
                        title = meta.get("title", "Resource")
                        parent_module = meta.get("parent_module", "")
                        
                        # Citation confidence: High for mediasite (course videos), medium for URLs
                        if link_type == "mediasite":
                            citation_confidence = "high"
                        else:
                            citation_confidence = "medium" if score > 0.35 else "low"
                        
                        embedded_docs.append({
                            "content": doc,
                            "metadata": meta,
                            "score": score * 0.9,  # Slight penalty vs course text
                            "source_file": f"{parent_module}: {title}" if parent_module else title,
                            "title": title,
                            "module": parent_module,
                            "week": "",
                            "source_type": "embedded",
                            "citation_confidence": citation_confidence,
                            "link_type": link_type,
                            "url": url,
                        })
            
            # --- MERGE RESULTS: Prioritize course > embedded > OER ---
            # STRATEGY: Ensure diverse source types (not all videos, not all text)
            # - Course materials (Blackboard text/PDFs): High priority for conceptual content
            # - Embedded resources (Mediasite videos): High priority for demonstrations
            # - OER (MIT Math for ML): Lower priority for supplementary theory
            
            # Sort by adjusted score with diversity weighting
            def sort_key(d):
                score = d.get("score", 0.0)
                source_type = d.get("source_type")
                link_type = d.get("link_type")
                
                # Boost by source type - calibrated to ensure top-5 includes both course text & videos
                if source_type == "course":
                    # Prioritize Blackboard course materials (text content with URLs)
                    if link_type == "blackboard":
                        boost = 0.40  # Highest priority: Course text with Blackboard URLs
                    else:
                        boost = 0.35  # Course text without URLs
                elif source_type == "embedded":
                    # Embedded resources (videos/external links)
                    if link_type == "mediasite":
                        boost = 0.25  # Videos rank well when relevant, but not above course text
                    else:
                        boost = 0.15  # Generic URLs (Wikipedia, etc.)
                else:  # OER
                    boost = 0.0
                    
                return score + boost
            
            # Sort all docs by adjusted score
            all_docs = course_docs + embedded_docs + oer_docs
            all_docs.sort(key=sort_key, reverse=True)
            
            # DIVERSITY FILTER: Ensure top-k includes BOTH course text AND videos (if available)
            # Strategy: Take top results, but reserve at least 1-2 slots for videos if they exist
            top_docs = []
            video_docs = [d for d in all_docs if d.get("link_type") == "mediasite"]
            non_video_docs = [d for d in all_docs if d.get("link_type") != "mediasite"]
            
            # If we have videos, ensure at least 1-2 make it into top-k
            if video_docs and len(video_docs) >= 2:
                # Take top 3 non-videos + top 2 videos
                top_docs = non_video_docs[:3] + video_docs[:2]
            elif video_docs and len(video_docs) == 1:
                # Take top 4 non-videos + 1 video
                top_docs = non_video_docs[:4] + video_docs[:1]
            else:
                # No videos - take all top docs
                top_docs = all_docs[:k]
            
            # Re-sort by original adjusted score to maintain relevance order
            top_docs.sort(key=sort_key, reverse=True)
            docs = top_docs[:k]
            
            # Deduplicate while preserving order
            unique_docs = []
            seen_keys = set()
            for d in docs:
                key = (d.get("source_file"), d.get("content")[:100])  # Use content snippet for dedup
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                unique_docs.append(d)
            
            # Return top k results (already sorted and deduped)
            docs = unique_docs[:k]
            
            # Count by source type
            course_count = sum(1 for d in docs if d.get("source_type") == "course")
            embedded_count = sum(1 for d in docs if d.get("source_type") == "embedded")
            oer_count = sum(1 for d in docs if d.get("source_type") == "oer")
            high_conf_count = sum(1 for d in docs if d.get("citation_confidence") == "high")
            logger.info(f"RAG: Retrieved {len(docs)} docs ({course_count} course, {embedded_count} media/URLs, {oer_count} OER) - {high_conf_count} high-confidence for inline citations")
            
            # Build metadata
            metadata = RAGMetadata(
                docs_retrieved=len(docs),
                sources_used=[d.get("source_file", "Unknown") for d in docs],
                retrieval_success=len(docs) > 0,
                has_comp237=course_count > 0,
            )
            
            return docs, metadata
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return [], RAGMetadata(
                docs_retrieved=0,
                sources_used=[],
                retrieval_success=False,
                has_comp237=False,
            )
    
    def format_context(
        self,
        docs: List[Dict[str, Any]],
        max_chars: int = 4000,
    ) -> str:
        """
        Format retrieved documents into a context string for prompts.
        Uses numbered references [1], [2], etc. that match the sources array.
        
        Args:
            docs: List of document dicts
            max_chars: Maximum characters to include
            
        Returns:
            Formatted context string with numbered references
        """
        if not docs:
            return "No course context available."
        
        pieces = []
        total_len = 0
        
        for idx, doc in enumerate(docs, start=1):
            source = doc.get("source_file", "Unknown")
            title = doc.get("title", "Document")
            content = doc.get("content", "").strip()
            score = doc.get("score", 0.0)
            
            # Use numbered reference [1], [2] that matches citation format
            header = f"[Source {idx}] {title}"
            source_info = f"File: {source} | Relevance: {score:.2f}"
            block = f"{header}\n{source_info}\nContent: {content}\n"
            block_len = len(block)
            
            if total_len + block_len > max_chars:
                break
            
            pieces.append(block)
            total_len += block_len
        
        return "\n\n---\n\n".join(pieces)
    
    def docs_to_sources(self, docs: List[Dict[str, Any]]) -> List[Source]:
        """Convert document dicts to Source schema objects with full metadata"""
        import re
        sources = []
        for doc in docs:
            title = doc.get("title", "Document")
            content = doc.get("content", "")
            module = doc.get("module", "")
            week = doc.get("week")
            
            # Generate description from content
            content_clean = content.strip()
            
            # CRITICAL FIX: Remove title duplication from description
            # Many sources start with "Title: [same as title field]" causing hover duplication
            # Step 1: Remove "Title:" or "Topic:" prefix if present
            content_clean = re.sub(r'^(Title|Topic):\s*', '', content_clean, flags=re.IGNORECASE)
            
            # Step 2: Check if content now starts with the title itself
            if content_clean.startswith(title):
                # Strip the title from the start of content
                content_clean = content_clean[len(title):].lstrip()
                # Remove any trailing/leading punctuation or whitespace
                content_clean = content_clean.lstrip(' .,;:')
            
            # Clean up broken starts (from chunking mid-sentence)
            # Run cleanup multiple times to handle cases like ". [Citation]"
            for _ in range(3):
                # Remove leading partial words like "tion.", "rectly.", "correct " etc.
                content_clean = re.sub(r'^[a-z]+[.,]\s*', '', content_clean)
                # Remove leading punctuation and whitespace
                content_clean = content_clean.lstrip(' .,;:')
                # Remove leading citations like "[Rich and Knight, 1991]"
                content_clean = re.sub(r'^\[[^\]]+\]\s*', '', content_clean)
                # Remove image references like "M8_Linear_Classifier_logo.png"
                content_clean = re.sub(r'\b[A-Z]\d+_[a-zA-Z_]+\.(png|jpg|gif)\s*', '', content_clean)
            
            # Take a reasonable chunk for description
            preview_len = 300
            if len(content_clean) <= preview_len:
                description = content_clean
            else:
                # Try to find a sentence break to avoid cutting mid-sentence
                chunk = content_clean[:preview_len]
                # Find last period in the chunk to end on a sentence if possible
                last_dot = chunk.rfind('.')
                if last_dot > 80:  # Increased from 50 for more context
                    description = chunk[:last_dot+1]
                else:
                    description = chunk + "..."
            
            # Final cleanup - ensure description doesn't start with lowercase fragment
            if description and len(description) > 0 and description[0].islower():
                # Try to find first capital letter to start properly
                cap_match = re.search(r'[A-Z]', description)
                if cap_match and cap_match.start() < 50:
                    description = description[cap_match.start():]
            
            sources.append(Source(
                title=title,
                source_file=doc.get("source_file", "Unknown"),
                collection=self.collection_name,
                score=doc.get("score", 0.0),
                # Increased content limit for better context in frontend
                content=content[:1500] + "..." if len(content) > 1500 else content,
                week=int(week) if week else None,
                module=module if module else None,
                description=description,
                # New multi-collection fields
                source_type=doc.get("source_type"),
                citation_confidence=doc.get("citation_confidence"),
                url=doc.get("url"),
                link_type=doc.get("link_type"),
            ))
        return sources


# Singleton instance for reuse
_rag_instance: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    """Get or create the singleton RAG retriever"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGRetriever()
    return _rag_instance
