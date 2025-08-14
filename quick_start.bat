@echo off
echo ========================================
echo AI Travel Assistant - Quick Start
echo ========================================
echo.

echo Checking dependencies...

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Please edit .env file with your API keys!
    echo   - AZURE_OPENAI_API_KEY
    echo   - AZURE_OPENAI_ENDPOINT
    echo   - PINECONE_API_KEY (optional)
    echo.
)

REM Install basic dependencies
echo Installing basic dependencies...
pip install -r requirements.txt --quiet

REM Check for ChromaDB segfault
echo.
echo Testing ChromaDB (this might cause segfault)...
python -c "import chromadb; print('ChromaDB OK')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  ChromaDB has issues. Setting to use In-Memory RAG...
    
    REM Update .env to use inmemory
    powershell -Command "(Get-Content .env) -replace 'VECTOR_DB_TYPE=chromadb', 'VECTOR_DB_TYPE=inmemory' | Set-Content .env" 2>nul
    if not exist ".env" (
        echo VECTOR_DB_TYPE=inmemory >> .env
    )
)

echo.
echo ========================================
echo Starting AI Travel Assistant...
echo ========================================
echo.
echo The app will open in your browser.
echo If you see errors, check:
echo   1. .env file has correct API keys
echo   2. Run scripts\fix_chromadb_segfault.bat if needed
echo.

streamlit run app.py