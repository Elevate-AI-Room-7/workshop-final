@echo off
echo ========================================
echo ChromaDB Segmentation Fault Fix
echo ========================================
echo.

echo Segmentation fault usually happens due to:
echo 1. Incomplete ChromaDB installation
echo 2. Missing Visual C++ Redistributable
echo 3. Python version incompatibility
echo 4. Corrupted ChromaDB data
echo.

echo [STEP 1] Uninstalling current ChromaDB...
pip uninstall chromadb -y

echo.
echo [STEP 2] Cleaning corrupted data...
if exist "chromadb_data" (
    echo Removing corrupted chromadb_data directory...
    rmdir /s /q chromadb_data
)

echo.
echo [STEP 3] Installing Visual C++ Redistributable dependencies...
echo Please install Visual C++ Redistributable if not already installed:
echo https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

echo.
echo [STEP 4] Installing specific ChromaDB version...
pip install chromadb==0.4.15 --no-cache-dir

if %errorlevel% neq 0 (
    echo.
    echo [FALLBACK 1] Trying ChromaDB with specific dependencies...
    pip install SQLAlchemy==1.4.49
    pip install chromadb==0.4.15 --no-deps --force-reinstall
    
    if %errorlevel% neq 0 (
        echo.
        echo [FALLBACK 2] Installing ChromaDB client only...
        pip install chromadb-client
        
        if %errorlevel% neq 0 (
            echo.
            echo ❌ ChromaDB installation failed completely.
            echo.
            echo SOLUTION: Use Pinecone or In-Memory instead
            echo Set in your .env file:
            echo   VECTOR_DB_TYPE=pinecone
            echo   # or
            echo   VECTOR_DB_TYPE=inmemory
            echo.
            pause
            exit /b 1
        )
    )
)

echo.
echo [STEP 5] Testing ChromaDB installation...
python -c "import chromadb; print('ChromaDB version:', chromadb.__version__); client = chromadb.Client(); print('✅ ChromaDB working!')" 2>nul

if %errorlevel% neq 0 (
    echo ❌ ChromaDB still not working properly.
    echo.
    echo RECOMMENDED SOLUTION:
    echo 1. Set VECTOR_DB_TYPE=inmemory in .env
    echo 2. Or use Pinecone: VECTOR_DB_TYPE=pinecone
    echo 3. The app will work without ChromaDB
    echo.
) else (
    echo ✅ ChromaDB fixed successfully!
    echo.
)

pause