FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    libgl1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Note: inswapper_128.onnx will be mounted as volume at runtime
# Check that the file exists before starting
CMD python -c "import os; print('Model exists:', os.path.exists('/app/inswapper_128.onnx'))" && python app.py
