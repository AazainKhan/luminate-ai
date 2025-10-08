"""
FAST Educate Mode - Simplified workflow for speed
Skips unnecessary agents, goes straight to retrieval + explanation
"""

from typing import Dict, Any, List
from llm_config import get_llm
import chromadb

def fast_educate_query(query: str, chroma_db=None, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    FAST educate mode - minimal agents for speed.
    
    Flow:
    1. Retrieve from ChromaDB
    2. Generate explanation with LLM
    3. Return formatted response
    
    No unnecessary classification, routing, or extra agents.
    """
    print(f"\n⚡ FAST EDUCATE MODE")
    print(f"📝 Query: {query}")
    
    # Step 1: Retrieve from ChromaDB (FAST - local database)
    retrieved_context = ""
    sources = []
    
    if chroma_db:
        try:
            results = chroma_db.query(
                query_texts=[query],
                n_results=3  # Just top 3 for speed
            )
            
            if results and results['documents'] and results['documents'][0]:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                
                retrieved_context = "\n\n".join(docs)
                
                for i, doc in enumerate(docs):
                    meta = metadatas[i] if i < len(metadatas) else {}
                    sources.append({
                        "title": meta.get("title", f"Source {i+1}"),
                        "content": doc[:200] + "...",
                        "module": meta.get("module", "Unknown")
                    })
                
                print(f"✅ Retrieved {len(docs)} course materials")
        except Exception as e:
            print(f"⚠️  ChromaDB error: {e}")
    
    # Step 2: Generate explanation (ONE LLM call)
    try:
        llm = get_llm(temperature=0.3)
        
        prompt = f"""You are an AI teaching assistant. Answer this student's question clearly and concisely.

Student Question: {query}

Course Materials (if relevant):
{retrieved_context[:2000] if retrieved_context else "No specific course materials found."}

Instructions:
1. Answer directly and clearly
2. Use course materials if relevant
3. Keep it concise (2-3 paragraphs)
4. Add 2 follow-up suggestions

Response:"""
        
        print(f"🤖 Generating explanation...")
        response = llm.invoke(prompt)
        explanation = response.content
        
        print(f"✅ Response generated")
        
        # Step 3: Format response (FAST - no extra LLM calls)
        return {
            "main_content": explanation,
            "response_type": "concept_explanation",
            "sources": sources,
            "related_concepts": [],
            "follow_up_suggestions": [
                "Try implementing this concept in code",
                "Ask about related topics"
            ],
            "metadata": {
                "intent": "concept_question",
                "complexity_level": "medium",
                "execution_time_ms": 0,
                "timestamp": "",
                "mode": "fast_educate"
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "main_content": f"I encountered an error: {str(e)}",
            "response_type": "error",
            "sources": [],
            "related_concepts": [],
            "follow_up_suggestions": [],
            "metadata": {"intent": "error", "mode": "fast_educate"}
        }


def fast_navigate_query(query: str, chroma_db=None) -> Dict[str, Any]:
    """
    FAST navigate mode - minimal processing for speed.
    
    Flow:
    1. Retrieve from ChromaDB
    2. Search YouTube (if enabled)
    3. Return results
    
    No unnecessary processing or extra agents.
    """
    print(f"\n⚡ FAST NAVIGATE MODE")
    print(f"📝 Query: {query}")
    
    # Step 1: Retrieve course materials
    top_results = []
    
    if chroma_db:
        try:
            results = chroma_db.query(
                query_texts=[query],
                n_results=5  # Top 5 results
            )
            
            if results and results['documents'] and results['documents'][0]:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                
                for i, doc in enumerate(docs):
                    meta = metadatas[i] if i < len(metadatas) else {}
                    top_results.append({
                        "title": meta.get("title", f"Result {i+1}"),
                        "content": doc[:300] + "...",
                        "module": meta.get("module", "Unknown"),
                        "type": "Course Material"
                    })
                
                print(f"✅ Found {len(top_results)} course materials")
        except Exception as e:
            print(f"⚠️  ChromaDB error: {e}")
    
    # Step 2: Search external resources (YouTube)
    external_resources = []
    
    try:
        from langgraph_workflows.agents.external_resources import search_youtube
        youtube_results = search_youtube(query, max_results=3)
        external_resources.extend(youtube_results)
        print(f"✅ Found {len(youtube_results)} YouTube videos")
    except Exception as e:
        print(f"⚠️  YouTube search error: {e}")
    
    # Step 3: Format response (no LLM call needed!)
    formatted_response = f"Found {len(top_results)} course materials and {len(external_resources)} external resources for: {query}"
    
    return {
        "formatted_response": formatted_response,
        "top_results": top_results,
        "related_topics": [],
        "external_resources": external_resources,
        "query_metadata": {
            "intent": "search",
            "entities": [],
            "complexity": "medium",
            "total_results": len(top_results),
            "mode": "fast_navigate"
        }
    }
