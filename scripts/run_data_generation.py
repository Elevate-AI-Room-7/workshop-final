#!/usr/bin/env python3
"""
Wrapper script để chạy data generation với proper setup
"""

import os
import sys
import subprocess

def main():
    print("🚀 AI Travel Assistant - Data Generation Setup")
    print("=" * 50)
    
    # Get script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    print(f"📁 Project root: {project_root}")
    
    # Change to project root
    os.chdir(project_root)
    print(f"📂 Changed to: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = os.path.join(project_root, '.env')
    if not os.path.exists(env_file):
        print("⚠️  .env file not found!")
        print("📝 Please create .env file with Azure OpenAI credentials")
        print("💡 See config/.env.example for template")
        return 1
    else:
        print("✅ .env file found")
    
    # Check if virtual environment is activated
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ Virtual environment: {venv_path}")
    else:
        print("⚠️  No virtual environment detected")
        print("💡 Consider using: source venv/bin/activate")
    
    # Try to install ChromaDB first
    print("\n🔧 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "scripts/install_chromadb.py"], check=True)
        print("✅ Dependencies installation completed")
    except subprocess.CalledProcessError:
        print("❌ Dependencies installation failed")
        print("🔧 Try manual installation: pip install -r requirements.txt")
        return 1
    
    # Run the actual data generation script
    print("\n📊 Running data generation...")
    try:
        # Set PYTHONPATH to include src directory
        env = os.environ.copy()
        src_path = os.path.join(project_root, 'src')
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path
        
        print(f"🐍 PYTHONPATH: {env['PYTHONPATH']}")
        
        result = subprocess.run([
            sys.executable, 
            "scripts/generate_sample_data.py"
        ], env=env, check=True)
        
        print("\n🎉 Data generation completed successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Data generation failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if all dependencies are installed")
        print("2. Verify .env file has correct Azure OpenAI credentials")
        print("3. Ensure ChromaDB is properly installed")
        print("4. Try running from project root directory")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        return 1

if __name__ == "__main__":
    exit(main())