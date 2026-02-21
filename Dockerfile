FROM python:3.14.3-slim-trixie@sha256:486b8092bfb12997e10d4920897213a06563449c951c5506c2a2cfaf591c599f

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY media/ ./media/
COPY frontend/ ./static/
COPY .en[v] ./

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
