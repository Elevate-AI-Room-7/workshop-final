"""
Debug script to check what RAG system is being used and test its methods
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("RAG SYSTEM DEBUG")
print("=" * 60)

# Check environment variables
print(f"VECTOR_DB_TYPE: {os.getenv('VECTOR_DB_TYPE', 'NOT SET')}")
print(f"PINECONE_API_KEY: {'SET' if os.getenv('PINECONE_API_KEY') else 'NOT SET'}")
print(f"CHROMADB_COLLECTION_NAME: {os.getenv('CHROMADB_COLLECTION_NAME', 'NOT SET')}")

print("\n" + "=" * 60)
print("IMPORTING TRAVEL PLANNER AGENT")
print("=" * 60)

try:
    from src.travel_planner_agent import TravelPlannerAgent
    print("✅ Successfully imported TravelPlannerAgent")
    
    print("\nCreating TravelPlannerAgent instance...")
    agent = TravelPlannerAgent()
    print("✅ Successfully created agent")
    
    # Check what RAG system was created
    rag_system = agent.rag_system
    print(f"\nRAG System Type: {type(rag_system).__name__}")
    print(f"RAG System Module: {type(rag_system).__module__}")
    
    # Check available methods
    print(f"\nAvailable methods:")
    methods = [method for method in dir(rag_system) if not method.startswith('_')]
    for method in sorted(methods):
        print(f"  - {method}")
    
    # Test specific methods
    print(f"\nTesting methods:")
    
    # Test upsert
    if hasattr(rag_system, 'upsert'):
        print("✅ Has upsert method")
    else:
        print("❌ Missing upsert method")
    
    # Test search
    if hasattr(rag_system, 'search'):
        print("✅ Has search method")
    else:
        print("❌ Missing search method")
    
    # Test delete
    if hasattr(rag_system, 'delete'):
        print("✅ Has delete method")
    else:
        print("❌ Missing delete method")
    
    # Test get_index_stats
    if hasattr(rag_system, 'get_index_stats'):
        print("✅ Has get_index_stats method")
        try:
            stats = rag_system.get_index_stats()
            print(f"  Stats: {stats}")
        except Exception as e:
            print(f"  Error getting stats: {e}")
    else:
        print("❌ Missing get_index_stats method")
    
    # Test if it has the old index attribute
    if hasattr(rag_system, 'index'):
        print(f"⚠️  Has 'index' attribute: {type(rag_system.index)}")
        if hasattr(rag_system.index, 'upsert'):
            print("  ⚠️  index.upsert exists (this might cause confusion)")
    else:
        print("✅ No 'index' attribute (good)")
    
    # Test a simple search
    print(f"\nTesting search functionality...")
    try:
        results = rag_system.search("test", top_k=1)
        print(f"✅ Search works: found {len(results)} results")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)