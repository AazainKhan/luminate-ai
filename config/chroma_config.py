from chromadb.config import Settings

CHROMA_SETTINGS = Settings(
    persist_directory="./chroma_db",
    anonymized_telemetry=False,
    allow_reset=False,
    is_persistent=True
)
