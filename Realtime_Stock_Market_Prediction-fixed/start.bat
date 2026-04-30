@echo off
echo 🚀 Starting AI Stock Predictor...

echo 📡 Starting FastAPI backend on port 8000...
cd backend
pip install -r requirements.txt -q
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"
start "FastAPI Backend" cmd /c "uvicorn app:app --host 0.0.0.0 --port 8000"
cd ..

echo ⏳ Waiting for backend...
timeout /t 3 /nobreak > nul

echo 🖥  Starting React frontend on port 5173...
cd frontend
if not exist .env (
    if exist .env.example (
        copy .env.example .env > nul
    )
)
call npm install --silent
start "React Frontend" cmd /c "npm run dev"
cd ..

echo ✅ Both services running!
echo    Backend:  http://127.0.0.1:8000
echo    Frontend: http://localhost:5173
pause
