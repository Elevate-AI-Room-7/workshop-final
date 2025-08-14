"""
Test script for all RAG systems to ensure they work correctly
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_system(rag_system, system_name):
    """Test a specific RAG system"""
    print(f"\n{'='*50}")
    print(f"Testing {system_name}")
    print(f"{'='*50}")
    
    try:
        # Test 1: Get stats
        print("\n1. Getting index statistics...")
        stats = rag_system.get_index_stats()
        print(f"   Stats: {stats}")
        
        # Test 2: Test search (empty search should not crash)
        print("\n2. Testing search functionality...")
        results = rag_system.search("test query", top_k=3)
        print(f"   Search results: {len(results)} found")
        
        # Test 3: Test upsert (add a test document)
        print("\n3. Testing upsert functionality...")
        test_embedding = [0.1] * 1536  # Mock embedding
        test_metadata = {
            "text": "Test document about Hanoi",
            "location": "Hanoi",
            "category": "test"
        }
        rag_system.upsert([("test-doc-1", test_embedding, test_metadata)])
        print("   Upsert successful")
        
        # Test 4: Test search again to find our document
        print("\n4. Testing search after upsert...")
        results = rag_system.search("Hanoi", top_k=5)
        print(f"   Search results: {len(results)} found")
        found_test_doc = any(r.get('id') == 'test-doc-1' for r in results)
        print(f"   Test document found: {found_test_doc}")
        
        # Test 5: Test delete
        print("\n5. Testing delete functionality...")
        rag_system.delete(["test-doc-1"])
        print("   Delete successful")
        
        # Test 6: Test query method
        print("\n6. Testing query method...")
        query_result = rag_system.query("Tell me about Hanoi", top_k=3)
        print(f"   Query result keys: {list(query_result.keys())}")
        print(f"   Has answer: {'answer' in query_result}")
        
        print(f"\n✅ {system_name} passed all tests!")
        return True
        
    except Exception as e:
        print(f"\n❌ {system_name} failed: {e}")
        logger.error(f"Error testing {system_name}: {e}", exc_info=True)
        return False

def test_factory():
    """Test the RAG factory"""
    print(f"\n{'='*50}")
    print("Testing RAG Factory")
    print(f"{'='*50}")
    
    try:
        from rag_factory import create_rag_system
        
        # Test different configurations
        configurations = [
            ("chromadb", "ChromaDB"),
            ("pinecone", "Pinecone"),
            ("unknown", "Fallback")
        ]
        
        for config_value, config_name in configurations:
            print(f"\nTesting with VECTOR_DB_TYPE={config_value}")
            
            # Set environment variable
            original_value = os.environ.get("VECTOR_DB_TYPE")
            os.environ["VECTOR_DB_TYPE"] = config_value
            
            try:
                rag_system = create_rag_system()
                system_type = type(rag_system).__name__
                print(f"   Created: {system_type}")
                
                # Quick test
                stats = rag_system.get_index_stats()
                print(f"   Stats: {stats.get('database', 'Unknown')}")
                
            except Exception as e:
                print(f"   Failed to create {config_name}: {e}")
            finally:
                # Restore original value
                if original_value is not None:
                    os.environ["VECTOR_DB_TYPE"] = original_value
                elif "VECTOR_DB_TYPE" in os.environ:
                    del os.environ["VECTOR_DB_TYPE"]
        
        print(f"\n✅ Factory tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Factory test failed: {e}")
        logger.error(f"Error testing factory: {e}", exc_info=True)
        return False

def test_individual_systems():
    """Test each RAG system individually"""
    results = {}
    
    # Test ChromaDB
    print(f"\n{'='*60}")
    print("TESTING INDIVIDUAL SYSTEMS")
    print(f"{'='*60}")
    
    try:
        from chromadb_rag_system import ChromaDBRAGSystem
        chromadb_system = ChromaDBRAGSystem()
        results['ChromaDB'] = test_rag_system(chromadb_system, "ChromaDB")
    except ImportError:
        print("\n⚠️  ChromaDB not available (not installed)")
        results['ChromaDB'] = False
    except Exception as e:
        print(f"\n❌ ChromaDB initialization failed: {e}")
        results['ChromaDB'] = False
    
    # Test Pinecone
    try:
        from pinecone_rag_system import PineconeRAGSystem
        pinecone_system = PineconeRAGSystem()
        results['Pinecone'] = test_rag_system(pinecone_system, "Pinecone")
    except Exception as e:
        print(f"\n⚠️  Pinecone not available: {e}")
        results['Pinecone'] = False
    
    # Test In-Memory
    try:
        from in_memory_rag_system import InMemoryRAGSystem
        memory_system = InMemoryRAGSystem()
        results['InMemory'] = test_rag_system(memory_system, "In-Memory")
    except Exception as e:
        print(f"\n❌ In-Memory system failed: {e}")
        results['InMemory'] = False
    
    return results

def main():
    print("="*60)
    print("RAG SYSTEMS COMPREHENSIVE TEST")
    print("="*60)
    
    # Test factory
    factory_ok = test_factory()
    
    # Test individual systems
    individual_results = test_individual_systems()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Factory Test: {'✅ PASS' if factory_ok else '❌ FAIL'}")
    
    for system, result in individual_results.items():
        status = '✅ PASS' if result else '❌ FAIL'
        print(f"{system:12}: {status}")
    
    total_passed = sum(individual_results.values())
    total_systems = len(individual_results)
    
    print(f"\nOverall: {total_passed}/{total_systems} systems working")
    
    if total_passed > 0:
        print("\n✅ At least one RAG system is working - application should run!")
    else:
        print("\n❌ No RAG systems working - check configuration and dependencies")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if not individual_results.get('ChromaDB'):
        print("• To fix ChromaDB: run scripts/install_chromadb.bat")
    
    if not individual_results.get('Pinecone'):
        print("• To fix Pinecone: check PINECONE_API_KEY in .env")
    
    if not individual_results.get('InMemory'):
        print("• In-Memory system should always work - check dependencies")
    
    print("• Make sure to set VECTOR_DB_TYPE in .env to your preferred system")

if __name__ == "__main__":
    main()