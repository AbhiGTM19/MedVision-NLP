# --- Stage 1: Builder ---
# This stage installs dependencies and builds necessary artifacts
FROM python:3.9-slim as builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

# --- Stage 2: Final Image ---
# This stage creates the final, lean production image
FROM python:3.9-slim

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Set the working directory
WORKDIR /home/app

# Copy installed packages, executables, and NLTK data from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /root/nltk_data/ /home/app/nltk_data/

# Set the NLTK_DATA environment variable
ENV NLTK_DATA=/home/app/nltk_data

# Copy the application code and set ownership
COPY --chown=app:app . .

# --- CRITICAL STEP: Train Both Models ---
# Run the training scripts to generate the model files inside the container
# This will create ./models/ and ./models/distilbert/
RUN python train.py
RUN python train_transformer.py

# Switch to the non-root user
USER app

# Expose the port the app will run on
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]