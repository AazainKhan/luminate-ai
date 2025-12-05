#!/usr/bin/env python3
"""
Load COMP237 concept graph into Neo4j for GraphRAG

This script:
1. Connects to Neo4j
2. Loads concept nodes and relationships
3. Creates indexes for fast queries
4. Verifies the load

Usage:
    cd backend
    python load_neo4j_graph.py
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neo4j settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "luminate_graph_pass")

# Paths
CONCEPT_GRAPH_PATH = Path(__file__).parent / "cleaned_data" / "processed" / "concept_graph.json"


def load_concept_graph() -> dict:
    """Load concept graph from JSON"""
    if not CONCEPT_GRAPH_PATH.exists():
        logger.error(f"Concept graph not found at {CONCEPT_GRAPH_PATH}")
        sys.exit(1)
    
    with open(CONCEPT_GRAPH_PATH, 'r') as f:
        return json.load(f)


def main():
    """Load concept graph into Neo4j"""
    print("=" * 60)
    print("Loading COMP237 Concept Graph into Neo4j")
    print("=" * 60)
    
    # Check if neo4j driver is available
    try:
        from neo4j import GraphDatabase
    except ImportError:
        logger.error("neo4j driver not installed. Run: pip install neo4j>=5.15.0")
        sys.exit(1)
    
    # Load concept graph
    logger.info(f"Loading concept graph from {CONCEPT_GRAPH_PATH}")
    graph_data = load_concept_graph()
    
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    concept_docs = graph_data.get("concept_documents", {})
    
    logger.info(f"Found {len(nodes)} concepts, {len(edges)} edges")
    
    # Connect to Neo4j
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        logger.info("✅ Connected to Neo4j")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neo4j: {e}")
        logger.info("Make sure Neo4j is running: docker compose up -d neo4j")
        sys.exit(1)
    
    try:
        with driver.session() as session:
            # Clear existing data
            logger.info("Clearing existing graph data...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Create constraints/indexes
            logger.info("Creating indexes...")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.id)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.id)")
            
            # Create concept nodes
            logger.info("Creating concept nodes...")
            for node in nodes:
                hierarchy = node.get("hierarchy_info", {})
                session.run("""
                    CREATE (c:Concept {
                        id: $id,
                        label: $label,
                        document_count: $doc_count
                    })
                """, 
                    id=node["id"], 
                    label=node["label"], 
                    doc_count=node.get("document_count", 0)
                )
            
            # Create relationships
            logger.info("Creating relationships...")
            has_subtopic_count = 0
            prereq_count = 0
            covers_count = 0
            
            for edge in edges:
                edge_type = edge.get("type", "")
                source = edge.get("source", "")
                target = edge.get("target", "")
                
                if edge_type == "HAS_SUBTOPIC":
                    result = session.run("""
                        MATCH (a:Concept {id: $source}), (b:Concept {id: $target})
                        CREATE (a)-[:HAS_SUBTOPIC]->(b)
                        RETURN count(*) as created
                    """, source=source, target=target)
                    if result.single()["created"] > 0:
                        has_subtopic_count += 1
                        
                elif edge_type == "PREREQUISITE_FOR":
                    result = session.run("""
                        MATCH (a:Concept {id: $source}), (b:Concept {id: $target})
                        CREATE (a)-[:PREREQUISITE_FOR]->(b)
                        RETURN count(*) as created
                    """, source=source, target=target)
                    if result.single()["created"] > 0:
                        prereq_count += 1
                        
                elif edge_type == "COVERS_CONCEPT":
                    # Create document node if needed and link to concept
                    result = session.run("""
                        MERGE (d:Document {id: $doc_id})
                        WITH d
                        MATCH (c:Concept {id: $concept_id})
                        CREATE (d)-[:COVERS]->(c)
                        RETURN count(*) as created
                    """, doc_id=source, concept_id=target)
                    if result.single()["created"] > 0:
                        covers_count += 1
            
            logger.info(f"  Created {has_subtopic_count} HAS_SUBTOPIC relationships")
            logger.info(f"  Created {prereq_count} PREREQUISITE_FOR relationships")
            logger.info(f"  Created {covers_count} COVERS relationships")
            
            # Verify load
            logger.info("\nVerifying graph...")
            result = session.run("""
                MATCH (c:Concept)
                RETURN count(c) as concept_count
            """)
            concept_count = result.single()["concept_count"]
            
            result = session.run("""
                MATCH ()-[r]->()
                RETURN count(r) as rel_count
            """)
            rel_count = result.single()["rel_count"]
            
            logger.info(f"✅ Graph loaded: {concept_count} concepts, {rel_count} relationships")
            
            # Test query
            logger.info("\nTest query: Finding prerequisites for 'neural_network'...")
            result = session.run("""
                MATCH (prereq:Concept)-[:PREREQUISITE_FOR]->(c:Concept {id: 'neural_network'})
                RETURN prereq.id as prereq, prereq.label as label
            """)
            prereqs = list(result)
            if prereqs:
                for r in prereqs:
                    logger.info(f"  ✅ Prerequisite: {r['label']} ({r['prereq']})")
            else:
                logger.info("  (No prerequisites found for neural_network)")
            
            # Test path query
            logger.info("\nTest query: Finding path from 'machine_learning' to 'gradient_descent'...")
            result = session.run("""
                MATCH path = shortestPath(
                    (start:Concept {id: 'machine_learning'})-[:PREREQUISITE_FOR|HAS_SUBTOPIC*..5]->(end:Concept {id: 'gradient_descent'})
                )
                RETURN [n in nodes(path) | n.label] as path_labels
            """)
            record = result.single()
            if record:
                path = record["path_labels"]
                logger.info(f"  ✅ Learning path: {' → '.join(path)}")
            else:
                logger.info("  (No path found)")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Neo4j graph load complete!")
        logger.info("=" * 60)
        logger.info("\nYou can explore the graph at: http://localhost:7474")
        logger.info("Username: neo4j")
        logger.info("Password: luminate_graph_pass")
        
    finally:
        driver.close()


if __name__ == "__main__":
    main()
