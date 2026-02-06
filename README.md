# 🎬 AI Video Factory (Kontenio)

**Automated Vertical Video Factory** - A "Zero-Touch" video automation pipeline that transforms raw talking-head footage into high-retention vertical videos (9:16).

## 📋 Overview

This project creates professional split-screen vertical videos by:
1. **Transcribing** raw video audio using OpenAI Whisper (API or Local)
2. **Analyzing** transcripts with GPT-4o/Gemini to generate contextual visual prompts
3. **Generating** AI images using DALL-E 3 or Imagen
4. **Rendering** the final video with Remotion (React-based video framework)
5. **Queueing**: All processing is handled in the background via Celery and Redis.

### Output Style
- **Split-Screen Layout**: Dynamic visuals (top) + talking head (bottom)
- **Glassmorphism Overlay**: Beautiful frosted-glass transcript display
- **Ken Burns Effect**: Subtle zoom animations on visuals
- **Professional Quality**: 1080x1920 @ 30fps, H.264 encoding

---

## 🚀 Quick Start (Containerized)

The easiest way to run Kontenio is using **Podman** (or Docker) through the centralized `Makefile`.

### Prerequisites
- [Podman](https://podman.io/) or Docker
- [Podman Compose](https://github.com/containers/podman-compose) or Docker Compose
- OpenAI / Gemini API keys

### Installation & Launch

```bash
# 1. Clone the project
# 2. Setup environment variables
cp .env.example .env  # Add your API keys here

# 3. Start the entire stack (DB, Redis, Web, Worker, Studio)
make up

# 4. Run database migrations inside the container
make migrate-db
```

### Access Points
- **Django Admin**: `http://localhost:8001/admin`
- **Remotion Studio**: `http://localhost:3000`
- **Media Server**: `http://localhost:9005` (Internal use for rendering)

---

## 🎯 Usage

### Centralized Control (CLI)

Use the `Makefile` commands to interact with the running containers:

```bash
# Put your raw video in backend/media/raw/
# Then run:

# Option A: Process in background (RECOMENDED)
make c-video-async INPUT="your_video.mp4"

# Option B: Process synchronously (wait for it)
make c-video INPUT="your_video.mp4"
```

### Manual rendering (Host side)
If you have the dependencies installed locally and want to render without containers:
```bash
make render-local
```

---

## 🛠️ Management Commands

| Command | Description |
| :--- | :--- |
| `make up` | Start all services (background) |
| `make down` | Stop and remove containers |
| `make logs` | View live logs from all services |
| `make status` | Check which containers are running |
| `make restart` | Restart all services |
| `make migrate-db` | Sync database schema |
| `make shell` | Open a bash terminal inside the web container |

---

## 📁 Project Structure

```
./
├── backend/            # Django Application
│   ├── core/           # Settings & Celery config
│   ├── video/          # Logic, Models, & Tasks
│   │   ├── tasks.py    # Celery background tasks
│   │   ├── services.py # Pipeline Orchestrator
│   └── media/          # Shared volumes for assets
├── src/                # Remotion (React) Components
├── compose.yaml        # Container orchestration
├── Dockerfile          # Unified build environment
└── Makefile            # Central control center
```

---

## 📦 Tech Stack

- **Backend**: Django 5.x, Celery 5.x
- **Broker/Cache**: Redis
- **Database**: PostgreSQL 15
- **Video Engine**: Remotion (React + Puppeteer)
- **Container**: Podman/Docker
- **AI**: OpenAI GPT-4o / Whisper, Google Gemini

---

## 🔧 Troubleshooting

### "podman-compose not found"
Ensure you are in an environment where `podman-compose` is installed (e.g., `pip install podman-compose`).

### "ModuleNotFoundError: No module named 'celery'"
This usually happens if you try to run `make dev` locally without installing the new dependencies. Use `make up` to run inside the container where everything is pre-installed.

### Rendering Timeouts
The first render might take longer as it builds the Remotion bundle. Check `make logs` to see if there are any Chromium-related errors.

---

## 📄 License
UNLICENSED - Private Project
