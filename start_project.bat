@echo off
echo ===================================================
echo     Starting ChandasAI Development Servers...
echo ===================================================

:: 1. Start the Python Backend in a new window
echo Launching Backend...
start "ChandasAI Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn api.app:app --reload"

:: 2. Start the Vite Frontend in a new window
echo Launching Frontend...
start "ChandasAI Frontend" cmd /k "cd frontend && npm run dev"

echo Done! Both terminals should pop up shortly.