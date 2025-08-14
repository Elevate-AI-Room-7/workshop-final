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
    echo   - WEATHER_API_KEY (optional)
    echo.
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Testing ChromaDB installation...
python -c "import chromadb; print('✅ ChromaDB installed successfully')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ ChromaDB installation failed. Installing...
    pip install chromadb --upgrade
    
    python -c "import chromadb; print('✅ ChromaDB installed successfully')" 2>nul
    if %errorlevel% neq 0 (
        echo ❌ ChromaDB still not working. Please install manually:
        echo pip install chromadb
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Starting AI Travel Assistant...
echo ========================================
echo.
echo 🔧 Vector Database: ChromaDB
echo 📂 Data Directory: ./chromadb_data
echo.
echo The app will open in your browser.
echo If you see errors, check your .env file for correct API keys.
echo.

streamlit run app.py