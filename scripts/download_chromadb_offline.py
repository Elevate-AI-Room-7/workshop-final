"""
Script to download ChromaDB wheel file for offline installation
This bypasses the need for Rust compilation
"""

import os
import sys
import platform
import requests
from pathlib import Path

def get_wheel_url():
    """Get the appropriate wheel URL based on system"""
    python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    
    # Determine platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        if machine in ["amd64", "x86_64"]:
            platform_tag = "win_amd64"
        else:
            platform_tag = "win32"
    elif system == "darwin":  # macOS
        if machine == "arm64":
            platform_tag = "macosx_11_0_arm64"
        else:
            platform_tag = "macosx_10_9_x86_64"
    else:  # Linux
        if machine in ["x86_64", "amd64"]:
            platform_tag = "manylinux_2_17_x86_64.manylinux2014_x86_64"
        else:
            platform_tag = "manylinux_2_17_aarch64.manylinux2014_aarch64"
    
    # ChromaDB version
    version = "0.4.15"
    
    # Try to find a compatible wheel
    base_url = f"https://files.pythonhosted.org/packages"
    
    # Common wheel patterns for ChromaDB
    wheel_patterns = [
        f"chromadb-{version}-py3-none-any.whl",  # Pure Python wheel
        f"chromadb-{version}-{python_version}-{python_version}-{platform_tag}.whl",
    ]
    
    # Return the most likely URL
    return f"https://pypi.org/project/chromadb/{version}/#files"

def download_with_proxy_bypass(url, filename):
    """Download file, trying to bypass proxy if needed"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Try without proxy first
    session = requests.Session()
    session.trust_env = False  # Ignore proxy environment variables
    
    try:
        print(f"Downloading from {url}...")
        response = session.get(url, headers=headers, stream=True, verify=False)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"Progress: {percent:.1f}%", end='\r')
        
        print(f"\nDownloaded to {filename}")
        return True
        
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def main():
    print("=" * 50)
    print("ChromaDB Offline Installer Helper")
    print("=" * 50)
    print()
    
    # Create wheels directory
    wheels_dir = Path("wheels")
    wheels_dir.mkdir(exist_ok=True)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()
    
    # Get wheel URL
    wheel_url = get_wheel_url()
    
    print("Manual download instructions:")
    print("-" * 50)
    print("1. Open this URL in your browser:")
    print(f"   {wheel_url}")
    print()
    print("2. Download the appropriate .whl file:")
    print("   - Look for 'chromadb-0.4.15-py3-none-any.whl' (preferred)")
    print("   - Or find one matching your Python version")
    print()
    print("3. Save it to the 'wheels' directory")
    print()
    print("4. Install with:")
    print("   pip install wheels/chromadb-*.whl")
    print()
    
    # Alternative: Install without ChromaDB
    print("Alternative: Use without ChromaDB")
    print("-" * 50)
    print("If you can't install ChromaDB, you can:")
    print("1. Set VECTOR_DB_TYPE=pinecone in your .env file")
    print("2. Or use the in-memory fallback (no persistence)")
    print()
    
    # Try downloading dependencies that don't need compilation
    print("Installing ChromaDB dependencies that don't require compilation...")
    print("-" * 50)
    
    deps = [
        "pydantic>=1.9",
        "requests>=2.28",
        "numpy>=1.21",
        "posthog>=2.4",
        "typing-extensions>=4.5",
        "pypika>=0.48",
        "tqdm>=4.65",
        "overrides>=7.3",
        "importlib-resources",
        "tenacity>=8.2",
        "PyYAML>=6.0",
        "orjson>=3.9",
    ]
    
    for dep in deps:
        os.system(f"pip install {dep}")
    
    print()
    print("Dependencies installed. ChromaDB core still needs manual installation.")
    print("Follow the manual download instructions above.")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    main()