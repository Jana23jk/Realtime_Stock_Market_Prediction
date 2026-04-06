#!/bin/bash
# Quick start script — runs backend and frontend together

echo "🚀 Starting AI Stock Predictor..."

# Start backend in background
echo "📡 Starting FastAPI backend on port 8000..."
cd backend
pip install -r requirements.txt -q
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"
uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
sleep 3

# Start frontend
echo "🖥  Starting React frontend on port 5173..."
cd frontend
cp -n .env.example .env 2>/dev/null || true
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both services running!"
echo "   Backend:  http://127.0.0.1:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both."

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
