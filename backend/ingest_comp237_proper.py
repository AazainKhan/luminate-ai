"""
ingest_comp237_proper.py - Ingest COMP237 course materials with correct Gemini embeddings

This script:
1. Deletes the old collection (if exists) 
2. Creates a new collection with Gemini embeddings (768-dim)
3. Ingests comprehensive COMP237 AI course content from Blackboard Export
4. Verifies the ingestion worked

Usage:
    cd backend
    source venv/bin/activate
    python ingest_comp237_proper.py
"""

import os
import sys
import logging
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
COLLECTION_NAME = "comp237_course_materials"
# Default to the user-provided ID if not in env, but allow override
BLACKBOARD_COURSE_ID = os.getenv("BLACKBOARD_COURSE_ID", "_11378_1") 
COURSE_ID = "COMP237"

EXPORT_DIR = Path(__file__).parent / "cleaned_data" / "ExportFile_COMP237"

def get_course_pk1():
    """
    Extract the Course PK1 ID from res00001.dat
    Returns: Course PK1 string (e.g., _11378_1) or default
    """
    res1_path = EXPORT_DIR / "res00001.dat"
    if not res1_path.exists():
        logger.warning(f"res00001.dat not found at {res1_path}, using default")
        return "_11378_1" # Default found in analysis
        
    try:
        with open(res1_path, 'r', encoding='utf-8') as f:
            content = f.read()
            root = ET.fromstring(content)
            course_id = root.get("id")
            if course_id:
                logger.info(f"Found Course PK1: {course_id}")
                return course_id
    except Exception as e:
        logger.error(f"Error extracting Course PK1: {e}")
        
    return "_11378_1"

def load_syllabus_data():
    """Load syllabus data from JSON map"""
    syllabus_path = Path(__file__).parent / "cleaned_data" / "syllabus_map.json"
    if not syllabus_path.exists():
        logger.warning(f"Syllabus map not found at {syllabus_path}")
        return []
    
    try:
        with open(syllabus_path, 'r') as f:
            data = json.load(f)
            return data.get("weeks", [])
    except Exception as e:
        logger.error(f"Error loading syllabus: {e}")
        return []

def parse_manifest(manifest_path):
    """Parse imsmanifest.xml to get resource mapping"""
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return {}

    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        
        # Namespaces in the XML
        ns = {'bb': 'http://www.blackboard.com/content-packaging/'}
        
        resources = {}
        # Find all resource elements (no default namespace)
        for res in root.findall(".//resource"):
            res_id = res.get("identifier")
            file_path = res.get("{http://www.blackboard.com/content-packaging/}file")
            title = res.get("{http://www.blackboard.com/content-packaging/}title")
            res_type = res.get("type")
            
            if res_id and file_path and res_type == "resource/x-bb-document":
                resources[res_id] = {
                    "file": file_path,
                    "title": title,
                    "type": res_type
                }
        return resources
    except Exception as e:
        logger.error(f"Error parsing manifest: {e}")
        return {}

def extract_content_from_dat(dat_path):
    """Extract content and metadata from a .dat file"""
    if not dat_path.exists():
        return None

    try:
        with open(dat_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # It's often XML-like but might have issues, try parsing as XML first
        try:
            root = ET.fromstring(content)
            # Extract Content ID
            bb_id = root.get("id") # e.g. _800667_1
            
            # Extract Body Text
            body_node = root.find(".//BODY/TEXT")
            if body_node is not None and body_node.text:
                raw_html = body_node.text
                soup = BeautifulSoup(raw_html, 'html.parser')
                text_content = soup.get_text(separator="\n").strip()
                return {
                    "bb_id": bb_id,
                    "content": text_content,
                    "raw_html": raw_html
                }
        except ET.ParseError:
            # Fallback for malformed XML: simple string search or BS4 on whole file
            logger.warning(f"XML parse error for {dat_path.name}, trying robust extraction")
            soup = BeautifulSoup(content, 'xml') # Try xml parser with BS4
            bb_id = soup.find("CONTENT")["id"] if soup.find("CONTENT") else None
            text_node = soup.find("TEXT")
            if text_node:
                html_soup = BeautifulSoup(text_node.text, 'html.parser')
                text_content = html_soup.get_text(separator="\n").strip()
                return {
                    "bb_id": bb_id,
                    "content": text_content,
                    "raw_html": text_node.text
                }
            
    except Exception as e:
        logger.error(f"Error extracting content from {dat_path.name}: {e}")
    
    return None

def load_blackboard_content():
    """Load content from the Blackboard Export"""
    manifest_path = EXPORT_DIR / "imsmanifest.xml"
    resources = parse_manifest(manifest_path)
    
    # Get Course PK1 for URL construction
    course_pk1 = get_course_pk1()
    
    documents = []
    
    logger.info(f"Found {len(resources)} document resources in manifest")
    
    for res_id, res_info in resources.items():
        dat_filename = res_info["file"]
        dat_path = EXPORT_DIR / dat_filename
        
        extracted = extract_content_from_dat(dat_path)
        if extracted and extracted["content"]:
            # Construct deep link URL
            # Format: https://luminate.centennialcollege.ca/ultra/courses/{course_id}/outline/edit/document/{content_id}?courseId={course_id}&view=content&state=view
            bb_content_id = extracted["bb_id"]
            deep_link = f"https://luminate.centennialcollege.ca/ultra/courses/{course_pk1}/outline/edit/document/{bb_content_id}?courseId={course_pk1}&view=content&state=view"
            
            # Create Document
            doc = Document(
                page_content=f"{res_info['title']}\n\n{extracted['content']}",
                metadata={
                    "course_id": COURSE_ID,
                    "bb_course_id": course_pk1,
                    "bb_content_id": bb_content_id,
                    "title": res_info["title"],
                    "res_id": res_id,
                    "source_file": dat_filename,
                    "content_type": "blackboard_document",
                    "url": deep_link
                }
            )
            documents.append(doc)
            
    return documents

def main():
    logger.info("=" * 60)
    logger.info("COMP237 Course Materials Ingestion (Blackboard Export)")
    logger.info("=" * 60)
    
    # Verify API key
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not set! Please set it in .env file")
        return
    
    # Connect to ChromaDB
    logger.info(f"Connecting to ChromaDB at {CHROMADB_HOST}:{CHROMADB_PORT}")
    client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    
    # Test connection
    try:
        client.heartbeat()
        logger.info("✅ ChromaDB connection successful")
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        return
    
    # Delete old collection if exists
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"🗑️ Deleted existing collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.info(f"Collection {COLLECTION_NAME} doesn't exist yet")
    
    # Initialize Gemini embeddings
    logger.info("Initializing Gemini embeddings (768-dim)...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )
    
    # Load Blackboard Content
    logger.info("Loading Blackboard content...")
    bb_documents = load_blackboard_content()
    logger.info(f"Loaded {len(bb_documents)} documents from Blackboard export")
    
    # Load Syllabus (keep this as it's structured well)
    syllabus_documents = []
    syllabus_weeks = load_syllabus_data()
    for i, week in enumerate(syllabus_weeks):
        week_num = week.get("week_number")
        topics = ", ".join(week.get("topics", []))
        content = f"Week {week_num}: {topics}"
        
        doc = Document(
            page_content=content,
            metadata={
                "course_id": COURSE_ID,
                "bb_course_id": BLACKBOARD_COURSE_ID,
                "bb_content_id": "syllabus", # Placeholder
                "title": f"Week {week_num} Syllabus",
                "module": f"Week {week_num}",
                "topic": "syllabus",
                "content_type": "syllabus",
                "source_filename": "syllabus_map.json"
            }
        )
        syllabus_documents.append(doc)
    
    all_documents = bb_documents + syllabus_documents
    
    if not all_documents:
        logger.error("No documents to ingest!")
        return

    # Generate embeddings
    logger.info("Generating embeddings...")
    texts = [doc.page_content for doc in all_documents]
    embedding_vectors = embeddings.embed_documents(texts)
    
    logger.info(f"✅ Generated {len(embedding_vectors)} embeddings")
    
    # Create collection with explicit metadata
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "l2", "course_id": COURSE_ID}
    )
    
    # Add documents to collection
    logger.info("Adding documents to ChromaDB...")
    ids = [f"doc_{i}" for i in range(len(all_documents))]
    metadatas = [doc.metadata for doc in all_documents]
    
    # Batch add to avoid hitting limits if any
    batch_size = 100
    for i in range(0, len(all_documents), batch_size):
        end = min(i + batch_size, len(all_documents))
        collection.add(
            ids=ids[i:end],
            embeddings=embedding_vectors[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end]
        )
        logger.info(f"Added batch {i}-{end}")
    
    logger.info(f"✅ Added {collection.count()} documents to collection")
    
    # Verify with test queries
    logger.info("\n" + "=" * 60)
    logger.info("Verification - Testing queries:")
    logger.info("=" * 60)
    
    test_queries = [
        "What is the Turing test?",
        "Explain backpropagation",
        "What are the ethics of AI?"
    ]
    
    for query in test_queries:
        results = collection.query(
            query_embeddings=embeddings.embed_query(query),
            n_results=1
        )
        if results['documents']:
            doc_content = results['documents'][0][0][:200] + "..."
            meta = results['metadatas'][0][0]
            logger.info(f"Query: {query}")
            logger.info(f"Match: {meta.get('title')} (ID: {meta.get('bb_content_id')})")
            logger.info(f"Content: {doc_content}\n")

if __name__ == "__main__":
    main()
