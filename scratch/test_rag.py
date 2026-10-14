import sys
import pprint

# Ensure chatbot-backend directory is on path
sys.path.insert(0, "chatbot-backend")

from app.rag.service import query_knowledge_base

if __name__ == "__main__":
    query = "What are the shipment packaging rules and delay policies?"
    print(f"--- Querying RAG Knowledge Base: '{query}' ---\n")
    
    result = query_knowledge_base(query)
    pprint.pprint(result)
