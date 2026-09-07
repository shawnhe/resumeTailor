# 1. Use your preferred base image
FROM node:24-slim

# 2. Set environment variables to automate setups 
# Fixes the Python PEP 668 error so you don't need a .venv inside the container
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 3. Update the OS and install Python + CA Certificates
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ca-certificates \
    git \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 4. Automatically install your required Python packages globally
RUN pip install --no-cache-dir openai pdfplumber python-docx pypdf fpdf2

# 5. Install Codex globally via npm
RUN npm install -g @openai/codex

# 6. Set your working directory inside the container
WORKDIR /app

# 7. Default to a plain shell that keeps the container alive in the background
CMD ["sh", "-c", "tail -f /dev/null"]
