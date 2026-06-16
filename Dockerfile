# --- Stage 1: Builder ---
# This stage installs dependencies and builds necessary artifacts
FROM python:3.11-slim as builder

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image ---
# This stage creates the final, lean production image
FROM python:3.11-slim


# Install Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces specifically requires the app to run as user 1000
RUN useradd -m -u 1000 appuser

# Set the working directory
WORKDIR /home/appuser/app

# Copy installed packages and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Set ENV to prod
ENV ENV=prod
ENV PYTHONPATH=/home/appuser/app/backend

# Copy the backend and frontend code and set ownership
COPY --chown=1000:1000 backend/ backend/
COPY --chown=1000:1000 frontend/ frontend/

# Switch to the non-root user
USER 1000

# Expose the port for Hugging Face Spaces
EXPOSE 7860

# Run the application with Uvicorn (FastAPI) from the backend directory
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers", "--forwarded-allow-ips", "*"]