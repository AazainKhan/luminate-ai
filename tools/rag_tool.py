from typing import List, Dict, Any
import chromadb
from config.chroma_config import CHROMA_SETTINGS

class RagTool:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=CHROMA_SETTINGS
        )
        self._cols = {}

    def _get(self, name: str):
        if name not in self._cols:
            self._cols[name] = self.client.get_or_create_collection(name=name)
        return self._cols[name]
    
    def retrieve(self, query: str, k: int = 4, score_threshold: float = 0.35):
        """
        Retrieve relevant documents from both course materials and OER resources.
        
        Args:
            query: The search query
            k: Number of results to return per collection
            score_threshold: Minimum similarity score (0-1) for a document to be included
            
        Returns:
            List of documents with text, score, and metadata
        """
        all_docs = []
        
        # Search in both collections
        for collection_name in ["course_comp237", "oer_resources"]:
            try:
                results = self._get(collection_name).query(
                    query_texts=[query],
                    n_results=k,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and results.get("documents"):
                    docs = results["documents"][0]
                    metas = results.get("metadatas", [[]])[0]
                    dists = results.get("distances", [[]])[0]
                    
                    for i, (text, meta, dist) in enumerate(zip(docs, metas, dists)):
                        # Convert distance to similarity score (1 - distance)
                        score = 1.0 - float(dist) if dist is not None else 0.0
                        if score >= score_threshold:
                            # Add collection info to metadata
                            meta = meta or {}
                            meta["collection"] = collection_name
                            all_docs.append({
                                "text": text,
                                "score": score,
                                "meta": meta
                            })
            except Exception as e:
                print(f"Error querying collection {collection_name}: {e}")
                continue
        
        # Sort by score in descending order and return top k results
        all_docs.sort(key=lambda x: x["score"], reverse=True)
        return all_docs[:k]


    def query(self, text: str, k: int, collections: list[str] = None) -> List[Dict[str, Any]]:
        """
        Query multiple collections and return combined results.
        
        Args:
            text: The query text
            k: Number of results to return per collection
            collections: List of collection names to query (defaults to all)
            
        Returns:
            List of document hits with metadata and scores
        """
        if collections is None:
            collections = ["course_comp237", "oer_resources"]
            
        hits: List[Dict[str, Any]] = []
        for cname in collections:
            try:
                col = self._get(cname)
                res = col.query(
                    query_texts=[text], 
                    n_results=k,
                    include=["documents", "metadatas", "distances"]
                )
                
                ids = res.get("ids", [[]])[0]
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                dists = res.get("distances", [[]])[0] if "distances" in res else [0.0] * len(ids)
                
                for i in range(len(ids)):
                    hits.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i] if i < len(metas) else {},
                        "distance": dists[i] if i < len(dists) else 0.0,
                        "collection": cname
                    })
            except Exception as e:
                print(f"Error querying collection {cname}: {e}")
                continue
        return hits
