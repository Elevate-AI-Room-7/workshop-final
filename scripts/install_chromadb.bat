@echo off
echo ========================================
echo ChromaDB Installation Helper
echo ========================================
echo.

REM Check Python version
python --version

echo.
echo Trying different installation methods...
echo.

REM Method 1: Try with pre-built wheel
echo [1] Trying pre-built wheel installation...
pip install chromadb-client --no-deps 2>NUL
if %errorlevel%==0 (
    echo Success with chromadb-client!
    goto :success
)

REM Method 2: Try without building from source
echo [2] Trying binary-only installation...
pip install --only-binary :all: chromadb 2>NUL
if %errorlevel%==0 (
    echo Success with binary-only!
    goto :success
)

REM Method 3: Try specific version that might have pre-built wheels
echo [3] Trying ChromaDB version 0.4.15 (has more pre-built wheels)...
pip install chromadb==0.4.15 2>NUL
if %errorlevel%==0 (
    echo Success with version 0.4.15!
    goto :success
)

REM Method 4: Install without tokenizers (which requires Rust)
echo [4] Installing ChromaDB dependencies separately...
pip install pydantic>=1.9 2>NUL
pip install requests>=2.28 2>NUL
pip install numpy>=1.21 2>NUL
pip install posthog>=2.4 2>NUL
pip install typing-extensions>=4.5 2>NUL
pip install onnxruntime>=1.14 2>NUL
pip install pypika>=0.48 2>NUL
pip install tqdm>=4.65 2>NUL
pip install overrides>=7.3 2>NUL
pip install importlib-resources 2>NUL
pip install graphlib-backport>=1.0 2>NUL
pip install bcrypt>=4.0 2>NUL
pip install typer>=0.9 2>NUL
pip install kubernetes>=28.1 2>NUL
pip install tenacity>=8.2 2>NUL
pip install PyYAML>=6.0 2>NUL
pip install mmh3>=4.0 2>NUL
pip install orjson>=3.9 2>NUL

echo.
echo [5] Trying ChromaDB with --no-build-isolation...
pip install chromadb --no-build-isolation 2>NUL
if %errorlevel%==0 (
    echo Success with no-build-isolation!
    goto :success
)

echo.
echo ========================================
echo ChromaDB installation failed!
echo ========================================
echo.
echo This is likely due to proxy blocking Rust download.
echo.
echo Solutions:
echo 1. Temporarily disable proxy:
echo    - Run: scripts\remove_proxy.bat
echo    - Then try: pip install chromadb
echo.
echo 2. Use offline wheel file:
echo    - Download .whl file from: https://pypi.org/project/chromadb/#files
echo    - Install: pip install path\to\chromadb.whl
echo.
echo 3. Use Docker/WSL2 with ChromaDB pre-installed
echo.
echo 4. Use only Pinecone (set VECTOR_DB_TYPE=pinecone in .env)
echo.
pause
exit /b 1

:success
echo.
echo ========================================
echo ChromaDB installed successfully!
echo ========================================
echo.
echo Testing import...
python -c "import chromadb; print('ChromaDB version:', chromadb.__version__)"
echo.
pause
exit /b 0