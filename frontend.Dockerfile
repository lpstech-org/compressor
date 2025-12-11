FROM python:3.12-slim

WORKDIR /app

COPY frontend ./frontend

RUN pip install --no-cache-dir streamlit requests

# Default API base inside Docker (points to backend service)
ENV API_BASE_URL=http://backend:8000/api

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
