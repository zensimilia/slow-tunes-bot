FROM python:3.10-slim

# Create directories
WORKDIR /app
RUN mkdir data

# Upgrade system and install dependencies
RUN echo "deb http://deb.debian.org/debian unstable main non-free contrib" >> /etc/apt/sources.list
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends sox libsox-fmt-all
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

# Install Python modules
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY . .

# Run bot
CMD ["python", "main.py"]
