
COMP-237 Prototype workspace created at: /mnt/data/COMP237_prototype

Files created:
- extracted/         : original extracted upload contents
- chunks.jsonl       : preprocessed text chunks ready for embedding
- embed_docs.py      : script to create embeddings and store in ChromaDB (run locally)
- fastapi_app.py     : FastAPI retrieval endpoint (prototype)
- chrome_extension/  : simple extension skeleton (popup.html, popup.js, manifest.json)

Important notes:
- This notebook environment has NO INTERNET, so embedding/model downloads must be run on your machine.
- To continue locally:
    1. Copy the project folder to your local machine (download links below).
    2. Install dependencies: pip install sentence-transformers chromadb fastapi uvicorn PyPDF2
    3. Run: python embed_docs.py --chunks chunks.jsonl --persist_dir chroma_index
    4. Then: python fastapi_app.py
    5. Load the chrome_extension folder as an unpacked extension in Chrome/Edge.

