# --- Stage 1: Builder ---
# This stage installs dependencies and builds necessary artifacts
FROM python:3.14-slim as builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt punkt_tab stopwords

# --- Stage 2: Final Image ---
# This stage creates the final, lean production image
FROM python:3.14-slim

# Hugging Face Spaces specifically requires the app to run as user 1000
RUN useradd -m -u 1000 appuser

# Set the working directory
WORKDIR /home/appuser/app

# Copy installed packages, executables, and NLTK data from the builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /root/nltk_data/ /home/appuser/nltk_data/

# Set the NLTK_DATA environment variable and set ENV to prod
ENV NLTK_DATA=/home/appuser/nltk_data
ENV ENV=prod

# Copy the application code and set ownership
COPY --chown=1000:1000 . .

# Switch to the non-root user
USER 1000

# Expose the port for Hugging Face Spaces
EXPOSE 7860

# Run the application with Uvicorn (FastAPI) instead of standard Gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]