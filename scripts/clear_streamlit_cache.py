"""
Clear Streamlit cache and reset session state
"""

import os
import shutil
import tempfile

def clear_streamlit_cache():
    """Clear Streamlit cache"""
    print("Clearing Streamlit cache...")
    
    # Common cache locations
    cache_dirs = [
        os.path.expanduser("~/.streamlit"),
        os.path.join(tempfile.gettempdir(), "streamlit"),
        ".streamlit/cache",
        "__pycache__"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared: {cache_dir}")
            except Exception as e:
                print(f"⚠️  Could not clear {cache_dir}: {e}")
    
    # Clear Python cache
    import sys
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('src.'):
            del sys.modules[module_name]
            print(f"✅ Cleared module: {module_name}")
    
    print("\n🔄 Cache cleared! Please restart your Streamlit app:")
    print("   streamlit run app.py")

if __name__ == "__main__":
    clear_streamlit_cache()