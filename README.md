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
