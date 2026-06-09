FROM python:3.11-slim

# System dependencies (Tesseract for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy project
COPY . .

# Expose API + Streamlit ports
EXPOSE 8000 8501

# Start both services (use supervisord or separate containers in prod)
CMD ["sh", "-c", \
     "uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 & \
      streamlit run frontend/dashboard.py --server.port 8501 --server.address 0.0.0.0"]
