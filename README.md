# AI PPT/PDF Compression Tool

This project is a local AI-assisted compressor for PowerPoint and PDF files.

- **Backend**: FastAPI (Python)  
- **Frontend**: Streamlit  
- **Containerization**: Docker / docker-compose  
- **Conversion**: LibreOffice (PPT/PPTX → PDF)  
- **Compression**: Ghostscript (PDF optimization)  
- **AI**: Ollama (LLM chooses compression settings and explains the result)

## Features

- Upload **PPT, PPTX, or PDF** via a Streamlit UI.
- If the file is larger than 50 MB:
  - PPT/PPTX → converted to PDF using LibreOffice.
  - PDF → compressed with Ghostscript using parameters suggested by an LLM.
- If the file is ≤ 50 MB, it can be left unchanged (configurable in code).
- Returns the compressed PDF and basic stats (original size, final size, ratio).

## Clone the repo  
1. In a terminal (Git Bash / PowerShell / CMD):
     git clone https://github.com/lpstech-org/compressor.git
2. See what changed
     git status
3. Stage changes
     git add .
4. Commit with a clear message
     git commit -m "Describe what you changed"
5. Push to GitHub
     git push

## Build and start with Docker
docker compose build
docker compose up -d

## Check containers 
docker compose ps

Expected:

compress-ai-ollama (Ollama server)
compress-ai-backend (FastAPI, port 8001)
compress-ai-frontend (Streamlit, port 8502)

## Useful endpoints to remember:
Health check: http://localhost:8001/api/health
Swagger UI: http://localhost:8001/docs
Frontend app: http://localhost:8502

## Project Structure

```text
backend/
  app/
    routes/
    services/
frontend/
  app.py
backend.Dockerfile
frontend.Dockerfile
docker-compose.yml
requirements.txt
