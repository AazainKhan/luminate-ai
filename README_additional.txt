
ADDITIONAL PROTOTYPE FILES ADDED
- Dockerfile
- docker-compose.yml
- requirements.txt

Quick local run instructions (recommended):
1. On your local machine, copy the COMP237_prototype folder.
2. (Optional but recommended) create a venv: python -m venv venv && source venv/bin/activate
3. Install requirements: pip install -r requirements.txt
4. Create embeddings and Chroma index:
   python embed_docs.py --chunks chunks.jsonl --persist_dir chroma_index
5. Run the API:
   python fastapi_app.py
6. Load chrome_extension/ as unpacked extension in Chrome (Developer mode).
7. Test by entering a query in the popup; it posts to http://localhost:8000/ask

If you'd like, I can also produce:
- A Docker image build script and sample .env handling for API keys
- An enhanced FastAPI app that calls a hosted LLM (OpenAI or local LLM) and performs streaming responses
- Unit tests and a simple CI config (GitHub Actions)

