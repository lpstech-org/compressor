FROM python:3.12-slim

# System dependencies for LibreOffice and Ghostscript
RUN apt-get update && \
    apt-get install -y libreoffice ghostscript && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
