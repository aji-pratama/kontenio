FROM python:3.11-slim-bookworm

# 1. Update & Install System Dependencies
# - ffmpeg: For video processing (MoviePy uses this)
# - imagemagick: For TextClip in MoviePy
# - fonts-*: Fonts for text rendering
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    fonts-roboto \
    procps \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow text rendering
RUN sed -i 's/domain="path" rights="none" pattern="@\*"/domain="path" rights="read|write" pattern="@\*"/g' /etc/ImageMagick-6/policy.xml

# 2. Setup Working Directory
WORKDIR /app

# 3. Setup Python Virtual Environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. Copy Dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 5. Copy Project Files
COPY . .

# 6. Create needed directories
RUN mkdir -p backend/media/raw backend/media/assets backend/media/output

# 7. Default Command
CMD ["tail", "-f", "/dev/null"]
