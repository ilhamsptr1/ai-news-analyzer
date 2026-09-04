FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (build-essential for compiling certain python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch first (CPU version to save massive amount of space and memory)
# Render/Railway don't provide GPUs on standard tiers anyway.
RUN pip install torch==2.0.1+cpu torchvision==0.15.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy model
RUN python -m spacy download xx_ent_wiki_sm

# Copy the rest of the application
COPY . .

# Run alembic migrations and then start the uvicorn server
# Use a script or chained command
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 10000"]
