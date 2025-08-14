#!/usr/bin/env python3
"""
Script để cài đặt ChromaDB và dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_package(package):
    """Check if package is installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    print("🔧 ChromaDB Installation Script")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return 1
    
    print(f"✅ Python version: {sys.version}")
    
    # Required packages
    packages = [
        ("chromadb", "chromadb>=0.4.0"),
        ("langchain", "langchain>=0.1.0"),
        ("langchain_openai", "langchain-openai>=0.0.5"),
        ("langchain_community", "langchain-community>=0.0.10"),
        ("openai", "openai>=1.6.0"),
        ("requests", "requests>=2.31.0"),
        ("python_dotenv", "python-dotenv>=1.0.0")
    ]
    
    print("\n📦 Checking packages...")
    need_install = []
    
    for pkg_import, pkg_install in packages:
        if check_package(pkg_import):
            print(f"✅ {pkg_import} - installed")
        else:
            print(f"❌ {pkg_import} - not installed")
            need_install.append(pkg_install)
    
    if not need_install:
        print("\n🎉 All packages are already installed!")
        return 0
    
    print(f"\n📥 Installing {len(need_install)} packages...")
    
    # Install missing packages
    failed = []
    for package in need_install:
        print(f"📦 Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            failed.append(package)
    
    if failed:
        print(f"\n❌ Failed to install: {', '.join(failed)}")
        print("\n🔧 Try manual installation:")
        for pkg in failed:
            print(f"  pip install {pkg}")
        return 1
    
    print("\n🎉 All packages installed successfully!")
    
    # Test ChromaDB import
    print("\n🧪 Testing ChromaDB import...")
    try:
        import chromadb
        print(f"✅ ChromaDB version: {chromadb.__version__}")
    except Exception as e:
        print(f"❌ ChromaDB import failed: {e}")
        return 1
    
    print("\n✅ ChromaDB installation completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())