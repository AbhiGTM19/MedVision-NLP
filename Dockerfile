# --- Stage 1: Build Stage ---
# Use a slim Python image as a base
FROM python:3.9-slim as builder

# Set the working directory in the container
WORKDIR /app

# Prevent Python from writing .pyc files and disable buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

# --- Stage 2: Final Stage ---
# Use a fresh, clean base image for the final product
FROM python:3.9-slim

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Set the working directory
WORKDIR /home/app

# --- THIS IS THE NEW CRITICAL FIX ---
# Give the 'app' user ownership of its home directory
RUN chown app:app /home/app

# Copy the installed packages and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
# Copy the downloaded NLTK data from the builder stage
COPY --from=builder /root/nltk_data/ /home/app/nltk_data/

# Copy the application source code AND set the owner to the 'app' user
COPY --chown=app:app . .

# Set environment variable for NLTK to find the data
ENV NLTK_DATA=/home/app/nltk_data

# Switch to the non-root user
USER app

# Run the training script to generate the model files
RUN python train.py

# Expose the port the app will run on
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]