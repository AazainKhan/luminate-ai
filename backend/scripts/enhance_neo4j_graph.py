#!/usr/bin/env python3
"""
Enhance Neo4j Knowledge Graph for Better Agentic Capabilities

This script:
1. Adds descriptions and categories to concept nodes
2. Creates Document-Concept relationships for better GraphRAG
3. Adds difficulty levels and learning sequence weights

Run: cd backend && python scripts/enhance_neo4j_graph.py
"""

import os
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "luminate_graph_pass")

# Enhanced concept metadata for better agentic responses
CONCEPT_ENHANCEMENTS = {
    "machine_learning": {
        "description": "Algorithms that learn patterns from data to make predictions or decisions without being explicitly programmed",
        "category": "core",
        "difficulty": 0.4,
        "week_introduced": 1,
        "keywords": ["supervised", "unsupervised", "training", "model", "prediction"]
    },
    "neural_network": {
        "description": "Computing systems inspired by biological neural networks, composed of interconnected layers of nodes",
        "category": "deep_learning",
        "difficulty": 0.6,
        "week_introduced": 8,
        "keywords": ["layers", "neurons", "weights", "activation", "feedforward"]
    },
    "gradient_descent": {
        "description": "Optimization algorithm used to minimize the loss function by iteratively adjusting model parameters",
        "category": "optimization",
        "difficulty": 0.7,
        "week_introduced": 9,
        "keywords": ["learning_rate", "optimization", "convergence", "backpropagation"]
    },
    "classification": {
        "description": "Supervised learning task of predicting discrete categorical labels for input data",
        "category": "supervised_learning",
        "difficulty": 0.4,
        "week_introduced": 3,
        "keywords": ["labels", "categories", "decision_boundary", "classifier"]
    },
    "regression": {
        "description": "Supervised learning task of predicting continuous numerical values",
        "category": "supervised_learning",
        "difficulty": 0.4,
        "week_introduced": 2,
        "keywords": ["linear", "polynomial", "prediction", "continuous"]
    },
    "deep_learning": {
        "description": "Subset of machine learning using neural networks with many hidden layers",
        "category": "advanced",
        "difficulty": 0.8,
        "week_introduced": 8,
        "keywords": ["CNN", "RNN", "deep", "representation_learning"]
    },
    "activation_functions": {
        "description": "Non-linear functions applied to neuron outputs to introduce non-linearity into the network",
        "category": "neural_network_components",
        "difficulty": 0.5,
        "week_introduced": 8,
        "keywords": ["ReLU", "sigmoid", "tanh", "softmax"]
    },
    "data_preprocessing": {
        "description": "Techniques to clean, normalize, and transform raw data before model training",
        "category": "fundamentals",
        "difficulty": 0.3,
        "week_introduced": 2,
        "keywords": ["normalization", "scaling", "encoding", "cleaning"]
    },
    "evaluation": {
        "description": "Methods to assess model performance using metrics like accuracy, precision, recall",
        "category": "fundamentals",
        "difficulty": 0.4,
        "week_introduced": 4,
        "keywords": ["accuracy", "precision", "recall", "f1", "confusion_matrix"]
    },
    "agents": {
        "description": "Autonomous entities that perceive their environment and take actions to achieve goals",
        "category": "ai_fundamentals",
        "difficulty": 0.5,
        "week_introduced": 5,
        "keywords": ["autonomous", "environment", "actions", "goals", "rational"]
    },
    "probability": {
        "description": "Mathematical framework for quantifying uncertainty, foundational to many ML algorithms",
        "category": "mathematics",
        "difficulty": 0.5,
        "week_introduced": 6,
        "keywords": ["bayes", "distribution", "likelihood", "prior", "posterior"]
    },
    "artificial_intelligence": {
        "description": "The field of creating systems that can perform tasks requiring human-like intelligence",
        "category": "foundation",
        "difficulty": 0.3,
        "week_introduced": 1,
        "keywords": ["intelligence", "automation", "learning", "reasoning"]
    },
    "search_algorithms": {
        "description": "Algorithms for finding solutions by exploring a search space systematically",
        "category": "ai_fundamentals",
        "difficulty": 0.4,
        "week_introduced": 5,
        "keywords": ["BFS", "DFS", "A*", "heuristic", "state_space"]
    },
    "nlp": {
        "description": "Field dealing with interactions between computers and human language",
        "category": "applications",
        "difficulty": 0.6,
        "week_introduced": 10,
        "keywords": ["text", "language", "tokenization", "embedding"]
    },
    "computer_vision": {
        "description": "Field enabling computers to interpret and understand visual information from images/videos",
        "category": "applications",
        "difficulty": 0.6,
        "week_introduced": 11,
        "keywords": ["images", "CNN", "object_detection", "recognition"]
    }
}


def main():
    """Enhance Neo4j graph with additional metadata"""
    print("=" * 60)
    print("Enhancing Neo4j Knowledge Graph for Agentic Capabilities")
    print("=" * 60)
    
    try:
        from neo4j import GraphDatabase
    except ImportError:
        logger.error("neo4j driver not installed")
        sys.exit(1)
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info("✅ Connected to Neo4j")
    except Exception as e:
        logger.error(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        with driver.session() as session:
            # Add enhanced properties to concepts
            logger.info("Adding descriptions and metadata to concepts...")
            enhanced_count = 0
            
            for concept_id, metadata in CONCEPT_ENHANCEMENTS.items():
                result = session.run("""
                    MATCH (c:Concept {id: $id})
                    SET c.description = $description,
                        c.category = $category,
                        c.difficulty = $difficulty,
                        c.week_introduced = $week,
                        c.keywords = $keywords
                    RETURN c.id as updated
                """,
                    id=concept_id,
                    description=metadata["description"],
                    category=metadata["category"],
                    difficulty=metadata["difficulty"],
                    week=metadata["week_introduced"],
                    keywords=metadata["keywords"]
                )
                if result.single():
                    enhanced_count += 1
            
            logger.info(f"  Enhanced {enhanced_count} concepts with metadata")
            
            # Create additional indexes for agent queries
            logger.info("Creating indexes for agentic queries...")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.category)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.difficulty)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.week_introduced)")
            
            # Verify enhancements
            result = session.run("""
                MATCH (c:Concept)
                WHERE c.description IS NOT NULL
                RETURN count(c) as enhanced_count
            """)
            count = result.single()["enhanced_count"]
            logger.info(f"✅ {count} concepts now have descriptions")
            
            # Show sample enhanced concept
            result = session.run("""
                MATCH (c:Concept {id: 'neural_network'})
                RETURN c.label as name, c.description as desc, c.difficulty as diff, c.keywords as keywords
            """)
            sample = result.single()
            if sample:
                logger.info(f"\nSample enhanced concept:")
                logger.info(f"  Name: {sample['name']}")
                logger.info(f"  Description: {sample['desc'][:80]}...")
                logger.info(f"  Difficulty: {sample['diff']}")
                logger.info(f"  Keywords: {sample['keywords']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Neo4j enhancement complete!")
        logger.info("=" * 60)
        
    finally:
        driver.close()


if __name__ == "__main__":
    main()


