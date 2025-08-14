"""
Test script to diagnose Pinecone connection issues
"""

import os
import sys
import time
import socket
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dns():
    """Test DNS resolution for Pinecone"""
    print("1. Testing DNS resolution...")
    try:
        ip = socket.gethostbyname('api.pinecone.io')
        print(f"   ✓ Pinecone API resolved to: {ip}")
        return True
    except socket.gaierror as e:
        print(f"   ✗ DNS resolution failed: {e}")
        return False

def test_connectivity():
    """Test basic HTTPS connectivity"""
    print("\n2. Testing HTTPS connectivity...")
    try:
        response = requests.get('https://api.pinecone.io', timeout=10, verify=False)
        print(f"   ✓ HTTPS connection successful (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"   ✗ HTTPS connection failed: {e}")
        return False

def test_pinecone_api():
    """Test Pinecone API with credentials"""
    print("\n3. Testing Pinecone API with credentials...")
    api_key = os.getenv("PINECONE_API_KEY")
    
    if not api_key:
        print("   ✗ PINECONE_API_KEY not found in environment")
        return False
    
    try:
        from pinecone import Pinecone
        
        # Try with custom connection settings
        pc = Pinecone(
            api_key=api_key,
            pool_threads=1,
            timeout=30
        )
        
        # Test list indexes
        indexes = pc.list_indexes()
        print(f"   ✓ Successfully connected to Pinecone")
        print(f"   ✓ Found {len(indexes.names())} indexes: {indexes.names()}")
        return True
        
    except Exception as e:
        print(f"   ✗ Pinecone API error: {e}")
        
        # Try alternative connection method
        print("\n   Trying alternative connection method...")
        try:
            import urllib3
            urllib3.disable_warnings()
            
            headers = {
                'Api-Key': api_key,
                'Accept': 'application/json'
            }
            
            response = requests.get(
                'https://api.pinecone.io/indexes',
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                print(f"   ✓ Alternative method successful")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"   ✗ API returned status {response.status_code}: {response.text}")
                return False
                
        except Exception as e2:
            print(f"   ✗ Alternative method also failed: {e2}")
            return False

def test_proxy_settings():
    """Check for proxy settings that might interfere"""
    print("\n4. Checking proxy settings...")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    
    found_proxy = False
    for var in proxy_vars:
        value = os.getenv(var)
        if value:
            print(f"   ! Found {var}: {value}")
            found_proxy = True
    
    if not found_proxy:
        print("   ✓ No proxy settings detected")
    else:
        print("   ! Proxy settings might interfere with connections")
        print("   Consider temporarily unsetting proxy variables")

def main():
    print("=" * 50)
    print("PINECONE CONNECTION DIAGNOSTIC")
    print("=" * 50)
    
    # Run tests
    dns_ok = test_dns()
    conn_ok = test_connectivity()
    api_ok = test_pinecone_api()
    test_proxy_settings()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if dns_ok and conn_ok and api_ok:
        print("✓ All tests passed - Pinecone connection is working")
    else:
        print("✗ Some tests failed - Troubleshooting needed")
        print("\nPossible solutions:")
        if not dns_ok:
            print("- Check your internet connection")
            print("- Try using a different DNS server (8.8.8.8)")
        if not conn_ok:
            print("- Check firewall/antivirus settings")
            print("- Try disabling VPN if using one")
            print("- Check if your network blocks HTTPS connections")
        if not api_ok:
            print("- Verify your PINECONE_API_KEY is correct")
            print("- Check if your API key has expired")
            print("- Try regenerating your API key in Pinecone console")
            print("- Check Pinecone service status at status.pinecone.io")

if __name__ == "__main__":
    main()