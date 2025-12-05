"""
GraphRAG Service - Hybrid retrieval using Neo4j knowledge graph + ChromaDB vector search

This module provides GraphRAG capabilities for the tutoring agent:
1. Vector search for semantic similarity (ChromaDB)
2. Graph traversal for concept relationships (Neo4j)
3. Combined context for more accurate and explainable responses

Based on research showing 35% improvement in RAG accuracy with hybrid approach.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Neo4j settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "luminate_graph_pass")

# Try to import neo4j, fall back to in-memory graph if not available
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j driver not installed. Using in-memory graph fallback.")


@dataclass
class ConceptNode:
    """Represents a concept in the knowledge graph"""
    id: str
    label: str
    document_count: int
    children: List[str]
    prerequisites: List[str]
    
    
@dataclass  
class GraphRAGResult:
    """Result from GraphRAG query combining vector + graph search"""
    vector_results: List[Dict]  # From ChromaDB
    graph_context: Dict  # From Neo4j/in-memory graph
    combined_context: str  # Merged context for LLM
    concept_path: List[str]  # Learning path suggestion
    related_concepts: List[str]  # Related topics


class Neo4jGraphService:
    """Neo4j-based knowledge graph service"""
    
    def __init__(self):
        self.driver = None
        if NEO4J_AVAILABLE:
            import time
            max_retries = 5
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
                    # Test connection
                    with self.driver.session() as session:
                        session.run("RETURN 1")
                    logger.info("✅ Connected to Neo4j")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Neo4j connection failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        logger.warning(f"Neo4j connection failed after {max_retries} attempts: {e}. Using in-memory fallback.")
                        self.driver = None
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def is_available(self) -> bool:
        return self.driver is not None
    
    def load_concept_graph(self, graph_data: Dict) -> bool:
        """Load concept graph from JSON into Neo4j"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Clear existing data
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create concept nodes
                for node in graph_data.get("nodes", []):
                    session.run("""
                        CREATE (c:Concept {
                            id: $id,
                            label: $label,
                            document_count: $doc_count
                        })
                    """, id=node["id"], label=node["label"], doc_count=node.get("document_count", 0))
                
                # Create relationships
                for edge in graph_data.get("edges", []):
                    if edge["type"] == "HAS_SUBTOPIC":
                        session.run("""
                            MATCH (a:Concept {id: $source}), (b:Concept {id: $target})
                            CREATE (a)-[:HAS_SUBTOPIC]->(b)
                        """, source=edge["source"], target=edge["target"])
                    elif edge["type"] == "PREREQUISITE_FOR":
                        session.run("""
                            MATCH (a:Concept {id: $source}), (b:Concept {id: $target})
                            CREATE (a)-[:PREREQUISITE_FOR]->(b)
                        """, source=edge["source"], target=edge["target"])
                
                logger.info(f"✅ Loaded {len(graph_data.get('nodes', []))} concepts into Neo4j")
                return True
        except Exception as e:
            logger.error(f"Failed to load graph into Neo4j: {e}")
            return False
    
    def get_concept_context(self, concept_id: str) -> Dict:
        """Get concept with its relationships from Neo4j"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Concept {id: $id})
                    OPTIONAL MATCH (c)-[:HAS_SUBTOPIC]->(child:Concept)
                    OPTIONAL MATCH (prereq:Concept)-[:PREREQUISITE_FOR]->(c)
                    OPTIONAL MATCH (c)-[:PREREQUISITE_FOR]->(next:Concept)
                    RETURN c.id as id, c.label as label, c.document_count as doc_count,
                           collect(DISTINCT child.id) as children,
                           collect(DISTINCT prereq.id) as prerequisites,
                           collect(DISTINCT next.id) as leads_to
                """, id=concept_id)
                
                record = result.single()
                if record:
                    return {
                        "id": record["id"],
                        "label": record["label"],
                        "document_count": record["doc_count"],
                        "children": [c for c in record["children"] if c],
                        "prerequisites": [p for p in record["prerequisites"] if p],
                        "leads_to": [l for l in record["leads_to"] if l]
                    }
                return {}
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return {}
    
    def find_learning_path(self, from_concept: str, to_concept: str, max_depth: int = 5) -> List[str]:
        """Find shortest learning path between concepts"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = shortestPath(
                        (start:Concept {id: $from})-[:PREREQUISITE_FOR|HAS_SUBTOPIC*..%d]->(end:Concept {id: $to})
                    )
                    RETURN [n in nodes(path) | n.id] as path
                """ % max_depth, from_concept=from_concept, to=to_concept)
                
                record = result.single()
                if record:
                    return record["path"]
                return []
        except Exception as e:
            logger.error(f"Learning path query failed: {e}")
            return []
    
    def get_related_concepts(self, concept_id: str, limit: int = 5) -> List[str]:
        """Get concepts related to the given concept"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Concept {id: $id})-[:HAS_SUBTOPIC|PREREQUISITE_FOR*1..2]-(related:Concept)
                    WHERE related.id <> $id
                    RETURN DISTINCT related.id as id, related.label as label
                    LIMIT $limit
                """, id=concept_id, limit=limit)
                
                return [record["id"] for record in result]
        except Exception as e:
            logger.error(f"Related concepts query failed: {e}")
            return []


class InMemoryGraphService:
    """In-memory fallback for when Neo4j is not available"""
    
    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}
        self.edges: List[Dict] = []
        self._load_from_file()
    
    def _load_from_file(self):
        """Load concept graph from JSON file"""
        graph_path = Path(__file__).parent.parent.parent / "cleaned_data" / "processed" / "concept_graph.json"
        if not graph_path.exists():
            logger.warning(f"Concept graph not found at {graph_path}")
            return
        
        try:
            with open(graph_path, 'r') as f:
                data = json.load(f)
            
            for node in data.get("nodes", []):
                hierarchy = node.get("hierarchy_info", {})
                self.nodes[node["id"]] = ConceptNode(
                    id=node["id"],
                    label=node["label"],
                    document_count=node.get("document_count", 0),
                    children=hierarchy.get("children", []),
                    prerequisites=hierarchy.get("prerequisites", [])
                )
            
            self.edges = data.get("edges", [])
            logger.info(f"✅ Loaded {len(self.nodes)} concepts from in-memory graph")
        except Exception as e:
            logger.error(f"Failed to load concept graph: {e}")
    
    def is_available(self) -> bool:
        return len(self.nodes) > 0
    
    def get_concept_context(self, concept_id: str) -> Dict:
        """Get concept with relationships"""
        if concept_id not in self.nodes:
            return {}
        
        node = self.nodes[concept_id]
        leads_to = [e["target"] for e in self.edges 
                    if e["source"] == concept_id and e["type"] == "PREREQUISITE_FOR"]
        
        return {
            "id": node.id,
            "label": node.label,
            "document_count": node.document_count,
            "children": node.children,
            "prerequisites": node.prerequisites,
            "leads_to": leads_to
        }
    
    def find_learning_path(self, from_concept: str, to_concept: str, max_depth: int = 5) -> List[str]:
        """Simple BFS to find learning path"""
        if from_concept not in self.nodes or to_concept not in self.nodes:
            return []
        
        # Build adjacency list
        adj = {}
        for edge in self.edges:
            if edge["type"] in ["PREREQUISITE_FOR", "HAS_SUBTOPIC"]:
                if edge["source"] not in adj:
                    adj[edge["source"]] = []
                adj[edge["source"]].append(edge["target"])
        
        # BFS
        visited = {from_concept}
        queue = [(from_concept, [from_concept])]
        
        while queue:
            current, path = queue.pop(0)
            if current == to_concept:
                return path
            if len(path) >= max_depth:
                continue
            
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def get_related_concepts(self, concept_id: str, limit: int = 5) -> List[str]:
        """Get related concepts"""
        if concept_id not in self.nodes:
            return []
        
        related = set()
        node = self.nodes[concept_id]
        
        # Add children and prerequisites
        related.update(node.children)
        related.update(node.prerequisites)
        
        # Add concepts this one leads to
        for edge in self.edges:
            if edge["source"] == concept_id:
                related.add(edge["target"])
            if edge["target"] == concept_id:
                related.add(edge["source"])
        
        related.discard(concept_id)
        return list(related)[:limit]


class GraphRAGService:
    """
    Main GraphRAG service combining vector search + knowledge graph
    
    Usage:
        service = GraphRAGService()
        result = service.query("What is backpropagation?", detected_concepts=["neural_network", "gradient_descent"])
    """
    
    def __init__(self):
        # Try Neo4j first, fall back to in-memory
        self.neo4j = Neo4jGraphService()
        self.in_memory = InMemoryGraphService()
        
        self.graph_service = self.neo4j if self.neo4j.is_available() else self.in_memory
        logger.info(f"GraphRAG using: {'Neo4j' if self.neo4j.is_available() else 'In-memory graph'}")
    
    def get_graph_context(self, concepts: List[str]) -> Dict:
        """Get knowledge graph context for detected concepts"""
        context = {
            "concepts": [],
            "prerequisites": set(),
            "next_topics": set(),
            "related": set()
        }
        
        for concept_id in concepts:
            concept_data = self.graph_service.get_concept_context(concept_id)
            if concept_data:
                context["concepts"].append(concept_data)
                context["prerequisites"].update(concept_data.get("prerequisites", []))
                context["next_topics"].update(concept_data.get("leads_to", []))
                context["related"].update(self.graph_service.get_related_concepts(concept_id))
        
        # Convert sets to lists
        context["prerequisites"] = list(context["prerequisites"])
        context["next_topics"] = list(context["next_topics"])
        context["related"] = list(context["related"])
        
        return context
    
    def get_learning_path(self, from_concept: str, to_concept: str) -> List[str]:
        """Find optimal learning path between concepts"""
        return self.graph_service.find_learning_path(from_concept, to_concept)
    
    def build_combined_context(
        self, 
        vector_results: List[Dict],
        graph_context: Dict,
        query: str
    ) -> str:
        """Build combined context string for LLM"""
        parts = []
        
        # Add vector search results
        if vector_results:
            parts.append("## Relevant Course Material")
            for i, result in enumerate(vector_results[:5], 1):
                title = result.get("title", "Untitled")
                module = result.get("module", "Unknown")
                content = result.get("content", "")[:500]
                parts.append(f"\n### [{i}] {title} (Module: {module})")
                parts.append(content)
        
        # Add graph context
        if graph_context.get("concepts"):
            parts.append("\n\n## Concept Relationships")
            for concept in graph_context["concepts"]:
                parts.append(f"\n**{concept['label']}**")
                if concept.get("prerequisites"):
                    prereqs = ", ".join(concept["prerequisites"])
                    parts.append(f"- Prerequisites: {prereqs}")
                if concept.get("leads_to"):
                    leads = ", ".join(concept["leads_to"])
                    parts.append(f"- Leads to: {leads}")
        
        # Add learning suggestions
        if graph_context.get("next_topics"):
            parts.append("\n\n## Suggested Next Topics")
            for topic in graph_context["next_topics"][:3]:
                parts.append(f"- {topic}")
        
        return "\n".join(parts)
    
    def query(
        self,
        query: str,
        vector_results: List[Dict],
        detected_concepts: List[str]
    ) -> GraphRAGResult:
        """
        Main query method combining vector search with graph traversal
        
        Args:
            query: User's question
            vector_results: Results from ChromaDB vector search
            detected_concepts: Concepts detected in the query
            
        Returns:
            GraphRAGResult with combined context
        """
        # Get graph context for detected concepts
        graph_context = self.get_graph_context(detected_concepts)
        
        # Build combined context
        combined_context = self.build_combined_context(vector_results, graph_context, query)
        
        # Find learning path if we have multiple concepts
        concept_path = []
        if len(detected_concepts) >= 2:
            concept_path = self.get_learning_path(detected_concepts[0], detected_concepts[-1])
        
        return GraphRAGResult(
            vector_results=vector_results,
            graph_context=graph_context,
            combined_context=combined_context,
            concept_path=concept_path,
            related_concepts=graph_context.get("related", [])
        )
    
    def close(self):
        """Clean up resources"""
        if self.neo4j:
            self.neo4j.close()


# Singleton instance
_graph_rag_service: Optional[GraphRAGService] = None


def get_graph_rag_service() -> GraphRAGService:
    """Get or create GraphRAG service singleton"""
    global _graph_rag_service
    if _graph_rag_service is None:
        _graph_rag_service = GraphRAGService()
    return _graph_rag_service


def load_graph_into_neo4j():
    """Utility function to load concept graph into Neo4j"""
    graph_path = Path(__file__).parent.parent.parent / "cleaned_data" / "processed" / "concept_graph.json"
    if not graph_path.exists():
        logger.error(f"Concept graph not found at {graph_path}")
        return False
    
    try:
        with open(graph_path, 'r') as f:
            graph_data = json.load(f)
        
        service = Neo4jGraphService()
        if service.is_available():
            return service.load_concept_graph(graph_data)
        else:
            logger.warning("Neo4j not available, skipping load")
            return False
    except Exception as e:
        logger.error(f"Failed to load graph: {e}")
        return False
