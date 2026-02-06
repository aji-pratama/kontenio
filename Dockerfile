FROM node:20-bookworm

# 1. Update & Install System Dependencies
# - python3, pip, venv: Untuk Django Backend
# - ffmpeg: Untuk pemrosesan video
# - chromium: Browser untuk Remotion render
# - fonts-*: Font agar rendering teks tidak kotak-kotak
# - procps: Untuk command 'ps', 'kill', dll
RUN apt-get update && apt-get install -y \
    python3-full \
    python3-pip \
    python3-venv \
    ffmpeg \
    chromium \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf fonts-liberation \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Working Directory
WORKDIR /app

# 3. Setup Python Virtual Environment (Optional but recommended practice)
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. Copy Dependencies Files first (Caching Strategy)
COPY package.json package-lock.json ./
COPY backend/requirements.txt ./backend/

# 5. Install Dependencies
RUN npm ci
RUN pip install --no-cache-dir -r backend/requirements.txt

# 6. Copy Project Files (Will be overwritten by volume mount in dev, but good for build)
COPY . .

# 7. Environment Variables for Remotion
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
ENV READ_ONLY_FS=true
# Fix for Chromium in Docker
ENV CHROMIUM_FLAGS="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu"

# 8. Create needed directories (Safe mkdir)
RUN mkdir -p backend/media/raw backend/media/output backend/media/props && \
    if [ ! -L public/media ] && [ ! -d public/media ]; then mkdir -p public/media; fi

# 9. Default Command (Keep container running)
CMD ["tail", "-f", "/dev/null"]
