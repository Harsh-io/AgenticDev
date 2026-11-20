# Local Setup Guide

Follow these instructions to run AgenticDev on your local machine.

## 1. Backend Setup

```powershell
# Navigate to the project root
cd D:\Evolve\AgenticDev

# Activate virtual environment
& .\backend\.venv\Scripts\Activate.ps1

# Start the FastAPI backend
uvicorn main:app --app-dir backend --reload --port 8000
```

Verify backend health at: [http://localhost:8000/health](http://localhost:8000/health)

## 2. Frontend Setup

```powershell
# Open a second terminal
cd D:\Evolve\AgenticDev\frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

Open the web interface at: [http://localhost:5173](http://localhost:5173)

