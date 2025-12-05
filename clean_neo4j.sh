#!/bin/bash
# Helper script to clean Neo4j data and logs
# Usage: ./clean_neo4j.sh

echo "🛑 Stopping Neo4j container..."
docker-compose stop neo4j

echo "🧹 Cleaning Neo4j data volume..."
docker volume rm luminate-ai_neo4j_data
docker volume rm luminate-ai_neo4j_logs

echo "✨ Neo4j environment cleaned."
echo "Run 'docker-compose up -d neo4j' to restart with a fresh database."
