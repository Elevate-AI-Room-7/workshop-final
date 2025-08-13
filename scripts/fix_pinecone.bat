@echo off
echo Fixing Pinecone package issue...

echo.
echo Step 1: Activating virtual environment...
call venv\Scripts\activate

echo.
echo Step 2: Uninstalling old pinecone-client...
pip uninstall pinecone-client -y

echo.
echo Step 3: Uninstalling any existing pinecone...
pip uninstall pinecone -y

echo.
echo Step 4: Installing correct pinecone package...
pip install pinecone>=3.0.0

echo.
echo Step 5: Installing other missing dependencies...
pip install langchain-community>=0.0.10

echo.
echo Fixed! You can now run: streamlit run app.py
echo.
pause