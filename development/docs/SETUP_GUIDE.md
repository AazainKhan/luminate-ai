# Luminate AI - Setup Guide

Quick start guide to get the Blackboard LMS data ingestion pipeline up and running.

## 📋 Prerequisites

- **Python 3.8+** (Check with: `python --version` or `python3 --version`)
- **pip** (Python package installer)
- **Blackboard course export** in the `extracted/` directory

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed beautifulsoup4-4.12.x pypdf-3.17.x python-docx-1.1.x ...
```

### Step 2: Validate Setup

```bash
python validate_setup.py
```

**What it checks:**
- ✅ Python version (3.8+)
- ✅ All dependencies installed
- ✅ Source directory exists
- ✅ Write permissions
- ✅ Disk space
- ✅ Sample file parsing

**Expected output:**
```
VALIDATION SUMMARY
========================================================
Python Version.............................. ✅ PASS
Dependencies................................ ✅ PASS
Source Directory............................ ✅ PASS
Write Permissions........................... ✅ PASS
Disk Space.................................. ✅ PASS
Sample Test................................. ✅ PASS
========================================================
✅ All checks passed! Ready to run ingestion pipeline.
```

### Step 3: Run the Pipeline

**Option A: Interactive Mode (Recommended for first run)**
```bash
python quick_start.py
```

Select option `5` to run all examples, or:
- `1` - Run full ingestion
- `2` - Explore output
- `3` - Prepare for ChromaDB
- `4` - Analyze issues

**Option B: Direct Command**
```bash
python ingest_clean_luminate.py
```

**Option C: Custom Configuration**
```bash
python ingest_clean_luminate.py \
  --source extracted/ExportFile_COMP237_INP \
  --output cleaned \
  --course-id _29430_1 \
  --course-name "Luminate"
```

### Step 4: Verify Output

Check that these were created:
```bash
ls -la cleaned/           # JSON files with chunks
ls -la graph_seed/        # graph_links.json
ls -la logs/              # ingestion.log, ingest_issues.txt
ls -la ingest_summary.json
```

### Step 5: (Optional) Load into ChromaDB

**Install ChromaDB:**
```bash
pip install chromadb
```

**Load and query:**
```bash
python chromadb_helper.py --load --interactive
```

Then type queries like:
- "What is artificial intelligence?"
- "Explain machine learning"
- "What are intelligent agents?"

Type `quit` to exit.

---

## 📁 What Gets Created

```
luminate-ai/
├── cleaned/                      # ✅ Cleaned JSON chunks
│   ├── Module01/
│   │   ├── topic1_1.json
│   │   └── topic1_2.json
│   ├── Module02/
│   │   └── overview.json
│   └── ...
├── graph_seed/
│   └── graph_links.json         # ✅ Document relationships
├── logs/
│   ├── ingestion.log            # ✅ Detailed processing log
│   └── ingest_issues.txt        # ✅ Errors/warnings
├── ingest_summary.json          # ✅ Statistics
└── chromadb_ready.json          # ✅ (if using quick_start.py)
```

---

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'bs4'"

**Solution:**
```bash
pip install -r requirements.txt
```

If that doesn't work:
```bash
pip install beautifulsoup4 pypdf python-docx python-pptx chardet tqdm
```

### Problem: "Source directory does not exist"

**Solution:**
Verify your export is in the right place:
```bash
ls -la extracted/ExportFile_COMP237_INP/
```

Or specify a different path:
```bash
python ingest_clean_luminate.py --source /path/to/your/export
```

### Problem: "Permission denied"

**Solution:**
Make scripts executable:
```bash
chmod +x ingest_clean_luminate.py validate_setup.py quick_start.py
```

Or run with python explicitly:
```bash
python ingest_clean_luminate.py
```

### Problem: No .dat files found

**Solution:**
Check that you're using a Blackboard export (not just a regular folder). The export should contain:
- `imsmanifest.xml`
- Multiple `res00001.dat`, `res00002.dat`, etc. files

### Problem: Pipeline runs but no chunks generated

**Check the logs:**
```bash
cat logs/ingest_issues.txt
cat logs/ingestion.log
```

**Common causes:**
- Empty .dat files
- Encoding issues
- XML parsing errors

---

## ⚡ Performance Tips

### For large courses (500+ documents):

1. **Run on a machine with SSD** - Significantly faster I/O
2. **Allocate enough RAM** - At least 2GB free
3. **Use Python 3.10+** - Faster XML parsing

### Expected processing times:
- Small course (~50 docs): 5-10 seconds
- Medium course (~200 docs): 20-40 seconds  
- Large course (~500 docs): 1-2 minutes

### To monitor progress:
The pipeline uses `tqdm` for progress bars:
```
Processing: 100%|████████████| 125/125 [00:35<00:00, 3.57file/s]
```

---

## 📊 Understanding the Output

### JSON Chunk Structure
Each file in `cleaned/` contains:
- **Metadata**: Course info, module, BB IDs, live URLs
- **Chunks**: 500-800 token segments with overlap
- **Tags**: Module name, title, keywords

### Graph Links
`graph_seed/graph_links.json` contains:
- `CONTAINS`: Parent-child relationships
- `NEXT_IN_MODULE`: Sequential ordering
- `PREV_IN_MODULE`: Reverse sequential

### Summary Report
`ingest_summary.json` shows:
- Total files processed/skipped
- Chunks and tokens generated
- Breakdown by module and file type
- Average tokens per file

---

## 🎯 Next Steps After Ingestion

### 1. Generate Embeddings
```python
# Example with OpenAI
import openai
import json

with open('chromadb_ready.json') as f:
    chunks = json.load(f)

for chunk in chunks:
    embedding = openai.Embedding.create(
        input=chunk['content'],
        model="text-embedding-ada-002"
    )
    chunk['embedding'] = embedding['data'][0]['embedding']
```

### 2. Build RAG Pipeline
```python
# Example retrieval
def retrieve_context(question, n=5):
    results = collection.query(
        query_texts=[question],
        n_results=n
    )
    
    # Return with live URLs for citations
    return [
        {
            'content': doc,
            'source': meta['live_lms_url'],
            'module': meta['module']
        }
        for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    ]
```

### 3. Integrate with LangGraph
```python
from langgraph.graph import Graph
import json

# Load graph structure
with open('graph_seed/graph_links.json') as f:
    links = json.load(f)

# Build knowledge graph
graph = Graph()
for link in links:
    graph.add_edge(
        link['source'],
        link['target'],
        relation=link['relation']
    )
```

---

## 🔐 Data Privacy & Security

### What's included in output:
- ✅ Text content from documents
- ✅ Document metadata (titles, dates)
- ✅ Blackboard IDs (for URL mapping)
- ✅ Module/course structure

### What's NOT included:
- ❌ Student data
- ❌ Grade information
- ❌ User credentials
- ❌ Private course materials (only exported content)

### Recommendations:
- Keep the `cleaned/` directory secure
- Don't commit to public repositories without review
- Use `.gitignore` (already configured) for sensitive data

---

## 🛠️ Advanced Configuration

### Customize Chunking
Edit `Config` class in `ingest_clean_luminate.py`:

```python
chunk_min_tokens: int = 300      # Smaller chunks
chunk_max_tokens: int = 600
chunk_overlap_percent: float = 0.3  # Less overlap
```

### Add Custom Boilerplate Patterns
```python
boilerplate_patterns: List[str] = [
    r'Blackboard\s+Learn',
    r'Your custom pattern here',
]
```

### Change Course URL Format
```python
base_url: str = "https://your.lms.com/courses"
```

### Add Custom File Types
```python
supported_extensions: Set[str] = {
    '.html', '.htm', '.pdf', '.docx', '.pptx', 
    '.txt', '.xml', '.md', '.dat',
    '.rtf'  # Add new type
}
```

Then create a parser:
```python
class RtfParser(FileParser):
    def parse(self, file_path: Path) -> str:
        # Your parsing logic
        return text
```

---

## 📞 Support Resources

### Logs to check:
1. `logs/ingestion.log` - Full processing log
2. `logs/ingest_issues.txt` - Errors and warnings
3. `ingest_summary.json` - Statistics

### Validation commands:
```bash
# Check setup
python validate_setup.py

# Test sample file
python -c "from ingest_clean_luminate import *; print('✅ Import successful')"

# Check dependencies
pip list | grep -E "beautifulsoup4|pypdf|python-docx|python-pptx|chardet|tqdm"
```

### Debug mode:
Edit `IngestionLogger` to change log level:
```python
self.logger.setLevel(logging.DEBUG)  # More verbose
ch.setLevel(logging.DEBUG)
```

---

## ✅ Success Checklist

After running the pipeline, verify:

- [ ] `ingest_summary.json` exists and shows processed files > 0
- [ ] `cleaned/` directory contains JSON files
- [ ] `graph_seed/graph_links.json` exists
- [ ] `logs/ingestion.log` shows no critical errors
- [ ] At least one JSON file contains chunks with content
- [ ] Live LMS URLs are properly formatted
- [ ] Blackboard IDs are extracted (check a few JSON files)

**Quick verification:**
```bash
# Count processed files
cat ingest_summary.json | grep "processed_files"

# Count chunks
cat ingest_summary.json | grep "total_chunks"

# Check a sample file
cat cleaned/*/*.json | head -50
```

---

## 🎓 Learning Resources

### Understanding the Pipeline:
1. Read `README.md` for full documentation
2. Review `ingest_clean_luminate.py` comments
3. Run `quick_start.py` to see examples
4. Check sample outputs in `cleaned/`

### Key Concepts:
- **Chunking**: Breaking documents into semantic segments
- **Embeddings**: Vector representations for semantic search
- **RAG**: Retrieval-Augmented Generation
- **Knowledge Graphs**: Structured document relationships

### Sample Queries (after ChromaDB setup):
```bash
python chromadb_helper.py --load --interactive

# Try these queries:
"What is the definition of AI?"
"Explain the Turing test"
"What are the types of intelligent agents?"
"Overview of machine learning"
```

---

**🎉 You're all set!** The pipeline is ready to process your Blackboard course exports and prepare them for AI-powered tutoring systems.

For detailed documentation, see `README.md`.
