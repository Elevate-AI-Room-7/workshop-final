#!/usr/bin/env python3
"""
Script để test Azure OpenAI credentials
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_vars():
    """Test environment variables"""
    print("🔧 Testing Environment Variables")
    print("=" * 40)
    
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_EMBEDDING_API_KEY",
        "AZURE_OPENAI_EMBEDDING_ENDPOINT"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the key for security
            if "API_KEY" in var:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    return all(os.getenv(var) for var in required_vars)

def test_azure_openai():
    """Test Azure OpenAI connection"""
    print("\n🤖 Testing Azure OpenAI Connection")
    print("=" * 40)
    
    try:
        from openai import AzureOpenAI
        
        # Get credentials
        api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
        
        print(f"🔑 Using API Key: {api_key[:8]}...{api_key[-4:] if api_key else 'None'}")
        print(f"🌐 Using Endpoint: {endpoint}")
        
        # Create client
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-07-01-preview"
        )
        
        print("✅ AzureOpenAI client created successfully")
        
        # Test embedding
        print("\n🧮 Testing embedding generation...")
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="Test embedding"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding generated successfully (dimension: {len(embedding)})")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI test failed: {e}")
        return False

def test_chromadb():
    """Test ChromaDB connection"""
    print("\n📚 Testing ChromaDB Connection")
    print("=" * 40)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Create ChromaDB client
        client = chromadb.PersistentClient(
            path="./chromadb_data",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        print(f"✅ ChromaDB client created successfully")
        print(f"📊 ChromaDB version: {chromadb.__version__}")
        
        # Test collection
        collection_name = "test-collection"
        try:
            client.delete_collection(collection_name)
        except:
            pass
            
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"✅ Test collection created: {collection_name}")
        
        # Clean up
        client.delete_collection(collection_name)
        print("✅ Test collection cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def main():
    print("🚀 Credentials and System Test")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_env_vars()
    
    # Test Azure OpenAI
    azure_ok = test_azure_openai() if env_ok else False
    
    # Test ChromaDB
    chroma_ok = test_chromadb()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"Azure OpenAI: {'✅' if azure_ok else '❌'}")
    print(f"ChromaDB: {'✅' if chroma_ok else '❌'}")
    
    if env_ok and azure_ok and chroma_ok:
        print("\n🎉 All tests passed! Ready to generate data.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())