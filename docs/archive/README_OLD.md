# Luminate AI - COMP-237 Intelligent Course Assistant# Luminate AI - Blackboard LMS Data Ingestion Pipeline



An AI-powered educational assistant for the COMP-237 (Artificial Intelligence) course at Centennial College. Features semantic search, intelligent tutoring, and seamless integration with Blackboard Learn.A comprehensive data engineering pipeline that transforms Blackboard LMS course exports into a structured dataset suitable for ChromaDB + LangGraph ingestion with live-link mapping to Blackboard URLs.



## 🌟 Features## Overview



- **Navigate Mode**: Find specific course materials using semantic searchThis pipeline processes raw Blackboard course exports and:

- **Educate Mode**: Get conceptual explanations and learning support (coming soon)- ✅ Extracts clean text from multiple file formats (HTML, PDF, DOCX, PPTX, TXT, XML, DAT)

- **Chrome Extension**: Quick access to course materials directly from Blackboard- ✅ Removes Blackboard boilerplate and navigation elements

- **External Resources**: YouTube, Wikipedia, and OER Commons integration- ✅ Extracts metadata and Blackboard document IDs

- **LangGraph Workflow**: Sophisticated multi-agent processing pipeline- ✅ Constructs live LMS URLs for each document

- **Vector Database**: ChromaDB-powered semantic search across 900+ course documents- ✅ Chunks text into 500-800 token segments with 50% overlap

- ✅ Generates structured JSON output ready for embedding

## 📁 Project Structure- ✅ Builds a relationship graph for LangGraph integration

- ✅ Provides comprehensive logging and statistics

```

luminate-ai/## Features

├── development/          # Main development workspace

│   ├── backend/         # FastAPI + LangGraph backend### 🔍 Multi-Format Support

│   │   ├── fastapi_service/   # API endpoints- **HTML/HTM**: BeautifulSoup-based parsing with heading preservation

│   │   ├── langgraph/         # Multi-agent workflow- **PDF**: Text extraction with pypdf

│   │   └── logs/              # Application logs- **DOCX**: Word document parsing with heading detection

│   └── frontend/        # Frontend applications (future)- **PPTX**: PowerPoint slide-by-slide extraction

├── chrome-extension/    # Chrome extension for Blackboard integration- **TXT/MD/XML**: Plain text with encoding detection

├── chromadb_data/      # Vector database storage- **DAT**: Blackboard XML format with metadata extraction

├── scripts/            # Utility scripts

├── tests/              # Test files### 🧹 Intelligent Cleaning

│   └── old_tests/      # Legacy test files- Removes Blackboard navigation headers, footers, and boilerplate

├── docs/               # Documentation- Normalizes whitespace and encoding (chardet-based detection)

│   └── implementation/ # Implementation notes and guides- Preserves document structure (headings → Markdown)

├── data/               # Data files- Filters out scripts, styles, and navigation elements

│   └── archive/        # Archived data and extracted files

├── logs/               # Application logs### 🔗 URL Mapping

└── .venv/              # Python virtual environment- Extracts Blackboard document IDs from content and filenames

```- Constructs live URLs in the format:

  ```

## 🚀 Quick Start  https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/{bb_doc_id}?courseId=_29430_1&view=content&state=view

  ```

### Prerequisites

### 📝 Smart Chunking

- Python 3.11+- Chunks text into 500-800 tokens (~2000-3200 characters)

- Node.js 18+ (for Chrome extension)- 50% overlap between chunks for context preservation

- Ollama (for local LLM)- Intelligent boundary detection (paragraph/sentence breaks)

- Chrome browser- Preserves chunk metadata and live URLs



### Backend Setup### 🗺️ Graph Relationships

- Builds hierarchical relationships (parent-child)

1. **Activate virtual environment**:- Creates sequential links (NEXT_IN_MODULE, PREV_IN_MODULE)

   ```bash- Outputs adjacency list for LangGraph integration

   source .venv/bin/activate- Tracks module organization and document ordering

   ```

### 📊 Comprehensive Logging

2. **Install dependencies**:- Detailed processing logs

   ```bash- Error and issue tracking

   pip install -r requirements.txt- Statistics by module and file type

   ```- Summary report with token counts



3. **Start the backend server**:## Installation

   ```bash

   cd development/backend### Prerequisites

   python fastapi_service/main.py- Python 3.8 or higher

   ```- pip package manager



   The server will start at `http://localhost:8000`### Setup



### Chrome Extension Setup1. **Clone or download the repository**

   ```bash

1. **Build the extension**:   cd /Users/aazain/Documents/GitHub/luminate-ai

   ```bash   ```

   cd chrome-extension

   npm install2. **Install dependencies**

   npm run build   ```bash

   ```   pip install -r requirements.txt

   ```

2. **Load in Chrome**:

   - Go to `chrome://extensions/`3. **Verify installation**

   - Enable "Developer mode"   ```bash

   - Click "Load unpacked"   python ingest_clean_luminate.py --help

   - Select `chrome-extension/dist` folder   ```



3. **Use the extension**:## Usage

   - Navigate to Blackboard course page

   - Click the Luminate AI icon### Basic Usage

   - Start asking questions!

Process the default Blackboard export:

## 📚 Documentation

```bash

- [Quick Start Guide](docs/QUICK_START.md)python ingest_clean_luminate.py

- [Extension Setup](docs/QUICK_START_EXTENSION.md)```

- [Implementation Notes](docs/implementation/)

- [Backend Improvements](docs/implementation/BACKEND_IMPROVEMENTS.md)This will:

- Read from `extracted/ExportFile_COMP237_INP/`

## 🏗️ Architecture- Output to `cleaned/`

- Generate graph links in `graph_seed/graph_links.json`

### Backend Components- Create logs in `logs/`

- Generate `ingest_summary.json`

- **FastAPI Service**: RESTful API endpoints

- **LangGraph Workflow**: Multi-agent orchestration### Advanced Usage

  - Understanding Agent

  - Retrieval Agent**Specify custom source directory:**

  - External Resources Agent```bash

  - Context Agentpython ingest_clean_luminate.py --source /path/to/blackboard/export

  - Formatting Agent```

- **ChromaDB**: Vector database with 917 embedded documents

- **Ollama Integration**: Local LLM for intelligent responses**Specify custom output directory:**

```bash

### Frontend Componentspython ingest_clean_luminate.py --output /path/to/output

```

- **Chrome Extension**: React-based side panel

- **UI Components**: shadcn/ui + Tailwind CSS**Specify custom course ID:**

- **Real-time Updates**: Streaming responses```bash

python ingest_clean_luminate.py --course-id _12345_1 --course-name "My Course"

## 🔧 Development```



### Running Tests**Full example:**

```bash

```bashpython ingest_clean_luminate.py \

# Run all tests  --source extracted/MyExport \

cd tests/old_tests  --output cleaned_data \

python test_all_queries.py  --course-id _29430_1 \

```  --course-name "COMP237"

```

### Checking Logs

## Output Structure

```bash

# Backend logs### Directory Layout

tail -f development/backend/logs/app.log

```

# LangGraph logsluminate-ai/

tail -f logs/langgraph.log├── cleaned/                          # Cleaned JSON files (mirrors source structure)

```│   ├── Module01/

│   │   ├── topic1.json

### Database Management│   │   └── topic2.json

│   ├── Module02/

```bash│   │   └── lecture1.json

# Check ChromaDB status│   └── ...

python scripts/chromadb_helper.py├── graph_seed/

│   └── graph_links.json              # Document relationship graph

# Re-ingest course materials├── logs/

python scripts/ingest_clean_luminate.py│   ├── ingestion.log                 # Detailed processing log

```│   └── ingest_issues.txt             # Errors and warnings

└── ingest_summary.json               # Statistics and summary

## 🌐 API Endpoints```



### Navigate Mode### JSON Output Format

```bash

POST http://localhost:8000/api/navigateEach processed file generates a JSON file with this structure:

{

  "query": "What is backpropagation?"```json

}{

```  "course_id": "_29430_1",

  "course_name": "Luminate",

### External Resources  "module": "Module 02 - Communication Models",

```bash  "file_name": "Lecture1.dat",

GET http://localhost:8000/api/external-resources?query=neural+networks  "content_type": ".dat",

```  "bb_doc_id": "_3960966_1",

  "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_3960966_1?courseId=_29430_1&view=content&state=view",

### Health Check  "title": "Welcome to the Course",

```bash  "created_date": "2024-06-07 14:47:17 EDT",

GET http://localhost:8000/health  "updated_date": "2024-11-11 17:07:01 EST",

```  "raw_text_length": 1523,

  "total_tokens": 380,

## 📊 System Status  "num_chunks": 1,

  "chunks": [

- **ChromaDB Documents**: 917 course materials    {

- **Vector Embeddings**: all-MiniLM-L6-v2 model      "chunk_id": "_3960966_1_chunk_000",

- **LLM Model**: Llama 3.2 (3B parameters)      "content": "## Welcome to the Course\n\nWelcome to COMP 237...",

- **Response Time**: ~2-5 seconds (depending on query complexity)      "tags": ["Module 02", "Welcome to the Course"],

      "live_lms_url": "https://luminate.centennialcollege.ca/ultra/...",

## 🎯 Roadmap      "token_count": 380,

      "chunk_index": 0,

- [x] Navigate Mode with semantic search      "total_chunks": 1

- [x] Chrome Extension integration    }

- [x] External resources (YouTube, Wikipedia, OER Commons)  ]

- [x] Scope detection for out-of-topic queries}

- [x] Query enhancement for AI/ML context```

- [ ] Educate Mode for conceptual learning

- [ ] Knowledge graph visualization### Graph Links Format

- [ ] Multi-course support

- [ ] Mobile appThe `graph_seed/graph_links.json` file contains relationships:



## 🤝 Contributing```json

[

This is a course project. For questions or issues, contact the development team.  {

    "source": "_1202503_1",

## 📝 License    "target": "_1202508_1",

    "relation": "CONTAINS",

Educational use only - Centennial College COMP-237 Course Project    "metadata": {"type": "hierarchy"}

  },

## 👥 Team  {

    "source": "_3960966_1",

Developed for COMP-237 (Artificial Intelligence) at Centennial College    "target": "_3960970_1",

    "relation": "NEXT_IN_MODULE",

---    "metadata": {"module": "Module 02"}

  }

**Last Updated**: October 5, 2025]

```

### Summary Report Format

The `ingest_summary.json` provides comprehensive statistics:

```json
{
  "pipeline_info": {
    "run_date": "2025-10-04T15:30:45.123456",
    "course_id": "_29430_1",
    "course_name": "Luminate",
    "source_directory": "extracted/ExportFile_COMP237_INP",
    "output_directory": "cleaned"
  },
  "statistics": {
    "total_files": 129,
    "processed_files": 125,
    "skipped_files": 4,
    "error_count": 0,
    "total_chunks": 456,
    "total_tokens": 234567,
    "avg_tokens_per_file": 1876.54
  },
  "by_file_type": {
    ".dat": 89,
    ".pdf": 15,
    ".html": 12,
    ".docx": 9
  },
  "by_module": {
    "Module 01": {
      "files": 15,
      "chunks": 67,
      "tokens": 34567
    },
    "Module 02": {
      "files": 18,
      "chunks": 89,
      "tokens": 45678
    }
  }
}
```

## Configuration

The pipeline can be configured by modifying the `Config` dataclass in `ingest_clean_luminate.py`:

```python
@dataclass
class Config:
    # Course identifiers
    course_id: str = "_29430_1"
    course_name: str = "Luminate"
    base_url: str = "https://luminate.centennialcollege.ca/ultra/courses"
    
    # Text processing
    chunk_min_tokens: int = 500      # Minimum tokens per chunk
    chunk_max_tokens: int = 800      # Maximum tokens per chunk
    chunk_overlap_percent: float = 0.5  # 50% overlap
    chars_per_token: float = 4.0     # Token estimation ratio
    
    # File processing
    supported_extensions: Set[str] = {'.html', '.htm', '.pdf', ...}
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    IngestionPipeline                        │
│                    (Main Orchestrator)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Parsers │ │ Chunker │ │ Graph   │
    │         │ │         │ │ Builder │
    └─────────┘ └─────────┘ └─────────┘
         │
    ┌────┴────┬────────┬─────────┬────────┐
    │         │        │         │        │
    ▼         ▼        ▼         ▼        ▼
  .DAT     .HTML     .PDF     .DOCX    .PPTX
```

### Key Classes

- **`IngestionPipeline`**: Main orchestrator
- **`Config`**: Centralized configuration
- **`FileParser`**: Base class for all parsers
  - `DatFileParser`: Blackboard XML format
  - `HtmlParser`: HTML/HTM files
  - `PdfParser`: PDF documents
  - `DocxParser`: Word documents
  - `PptxParser`: PowerPoint presentations
  - `TextParser`: Plain text files
- **`TextChunker`**: Intelligent text segmentation
- **`GraphBuilder`**: Relationship graph construction
- **`ManifestParser`**: IMS manifest parsing
- **`IngestionLogger`**: Logging and issue tracking

## Workflow

1. **Initialization**
   - Load configuration
   - Setup logging
   - Initialize parsers and chunker

2. **Manifest Parsing**
   - Parse `imsmanifest.xml`
   - Build course structure map

3. **File Collection**
   - Recursively scan source directory
   - Filter by supported extensions

4. **File Processing** (for each file)
   - Parse based on file type
   - Extract metadata
   - Clean text (remove boilerplate)
   - Extract Blackboard IDs
   - Construct live URLs
   - Chunk text with overlap
   - Generate chunk metadata

5. **Graph Building**
   - Track document relationships
   - Build hierarchical links
   - Create sequential links

6. **Output Generation**
   - Save JSON files (mirroring structure)
   - Save graph links
   - Save summary statistics
   - Save issue log

## Troubleshooting

### Common Issues

**Issue: "Missing required library"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue: "Source directory does not exist"**
```bash
# Solution: Verify path or specify correct path
python ingest_clean_luminate.py --source /correct/path
```

**Issue: "No text content extracted"**
- Check file encoding
- Verify file isn't corrupted
- Check logs/ingest_issues.txt for details

**Issue: "XML parse error"**
- DAT file may be malformed
- Check source export integrity
- Review logs for specific error

### Debugging

Enable detailed logging by checking:
```bash
# View full log
cat logs/ingestion.log

# View issues only
cat logs/ingest_issues.txt

# Check summary
cat ingest_summary.json
```

## Advanced Topics

### Custom Parsers

To add support for new file types:

```python
class CustomParser(FileParser):
    """Parser for custom file type."""
    
    def parse(self, file_path: Path) -> str:
        """Parse custom file and extract text."""
        # Your parsing logic here
        return cleaned_text
```

### Modifying Chunking Strategy

Adjust chunking parameters in Config:

```python
chunk_min_tokens: int = 300  # Smaller chunks
chunk_max_tokens: int = 500
chunk_overlap_percent: float = 0.3  # Less overlap
```

### Adding Custom Relationships

Extend `GraphBuilder` to add new relationship types:

```python
def add_related_topics(self, doc_id: str, related_ids: List[str]):
    """Add RELATED_TO relationships."""
    for related_id in related_ids:
        self.links.append(GraphLink(
            source=doc_id,
            target=related_id,
            relation="RELATED_TO",
            metadata={"type": "semantic"}
        ))
```

## Next Steps

After running the ingestion pipeline:

1. **Embedding Generation**: Use the JSON chunks to generate embeddings with your preferred model (e.g., OpenAI, Sentence Transformers)

2. **ChromaDB Ingestion**: Load chunks into ChromaDB collection:
   ```python
   import chromadb
   
   client = chromadb.Client()
   collection = client.create_collection("luminate_course")
   
   # Add chunks with metadata
   for chunk in chunks:
       collection.add(
           documents=[chunk['content']],
           metadatas=[chunk],
           ids=[chunk['chunk_id']]
       )
   ```

3. **LangGraph Integration**: Use the graph links to build a knowledge graph:
   ```python
   from langgraph import Graph
   
   # Load graph links
   with open('graph_seed/graph_links.json') as f:
       links = json.load(f)
   
   # Build graph
   graph = Graph()
   for link in links:
       graph.add_edge(link['source'], link['target'], link['relation'])
   ```

4. **RAG Pipeline**: Implement retrieval-augmented generation using the structured data and live URLs for source attribution.

## Performance

- **Processing Speed**: ~10-20 files/second (varies by file size and type)
- **Memory Usage**: ~100-500MB peak (depends on document sizes)
- **Output Size**: ~2-5x larger than source (due to metadata and chunking)

Typical processing times:
- Small course (~50 documents): 5-10 seconds
- Medium course (~200 documents): 20-40 seconds
- Large course (~500 documents): 1-2 minutes

## License

This project is part of the Luminate AI educational technology platform.

## Support

For issues, questions, or contributions:
- Check logs in `logs/` directory
- Review `ingest_summary.json` for statistics
- Examine `logs/ingest_issues.txt` for specific problems

## Changelog

### Version 1.0.0 (2025-10-04)
- Initial release
- Multi-format support (HTML, PDF, DOCX, PPTX, TXT, XML, DAT)
- Intelligent chunking with overlap
- Blackboard ID extraction and URL mapping
- Graph relationship building
- Comprehensive logging and statistics
- Configurable pipeline with CLI interface
