# Deployment Guide

This guide describes how to deploy AgenticDev across supported hosting platforms.

## Vercel Deployment

1. **Root Directory**: Configure repository root.
2. **Build Settings**:
   - Framework preset: Vite
   - Root directory for frontend: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
3. **Environment Variables**:
   - `GROQ_API_KEY`: Groq API key for agent inference
   - `GROQ_MODEL`: Model ID (e.g. `llama-3.3-70b-versatile` or `qwen/qwen3.8-27b`)
   - `VITE_API_URL`: Backend API URL (defaults to production FastAPI domain)

## Backend FastAPI Deployment

Deploy `backend/main.py` using Uvicorn or Gunicorn with Uvicorn workers:

```bash
uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

