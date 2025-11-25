# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files (your entire backend)
COPY . .

# Hugging Face Spaces default port = 7860
EXPOSE 7860

# Run the app on the correct port
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
