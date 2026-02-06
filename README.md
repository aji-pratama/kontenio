# 🎬 Kontenio: AI Video Factory

**The Open-Source Bulk Content "Talking Head" Generator.**

Kontenio is a high-performance, containerized video automation pipeline designed to transform raw vertical footage (talking head) into high-retention, split-screen masterpieces at scale. It leverages AI for transcription, visual mapping, and image generation, powered by a robust React-based rendering engine.

---

## 🏗️ Core Architecture

Kontenio is built for **Automated Bulk Processing**. Unlike manual editors, it uses a "Queue-First" architecture:

1.  **Transcription**: Extracts audio via OpenAI Whisper or Gemini.
2.  **Contextual Mapping**: LLM (GPT-4o/Gemini) analyzes the speech to generate visual prompts for B-Roll.
3.  **Image Synthesis**: DALL-E 3 or Imagen creates high-quality visuals for the top screen.
4.  **React Rendering**: [Remotion](https://remotion.dev) takes over to render the final H.264 video with glassmorphism overlays, Ken Burns effects, and dynamic captions.
5.  **Auto-Pilot**: A built-in scheduler (Celery Beat) automatically picks up pending uploads and processes them.

---

## 🚀 Dev Quick Start

### 1. Prerequisites
- **Podman** (preferred) or **Docker**
- OpenAI and/or Google Gemini API Keys

### 2. Setup & Boot
```bash
# 1. Clone the repo
git clone https://github.com/your-repo/kontenio.git && cd kontenio

# 2. Environment Setup
cp .env.example .env  # Add your API_KEYS here

# 3. Launch the Stack
make up

# 4. Prepare Database
make migrate-db
```

### 3. Dashboard Access Points
- 🌐 **Django Admin**: `http://localhost:8001/admin` (Manage projects)
- 🌸 **Flower**: `http://localhost:5555` (Celery monitoring & stats)
- 📽️ **Remotion Studio**: `http://localhost:3000` (Direct UI editing)

---

## 🛠️ Performance & Scalability

- **Background Workers**: Scaling processing power is as simple as adding more Celery workers.
- **Auto-Pick Scheduler**: Upload 100 videos to the `raw/` folder, and Celery Beat will automatically queue and process them.
- **Monitoring**: Integration with Flower provides real-time visibility into the rendering pipeline.
- **Fail-Safe**: Robust symlink handling and dedicated media servers (`:9005`) ensure stable rendering in headless environments.

---

## �️ Management (Makefile)

The `Makefile` is the heart of Kontenio's developer experience:

| Command | Description |
| :--- | :--- |
| `make up` | Boot the entire stack (Database, Redis, Web, Worker, Beat, Flower, Studio) |
| `make down` | Tear down the stack |
| `make build` | Rebuild images after changing requirements |
| `make logs-worker` | Tail logs specifically for the video processing engine |
| `make logs-flower` | Monitor Celery Flower dashboard logs |
| `make c-video-async` | Trigger a video job via CLI: `make c-video-async INPUT="clip.mp4"` |
| `make retry-failed` | (Via Admin) Reset failed projects to pending for auto-processing |

---

## 📦 Tech Stack

- **Backend**: Django & Celery (Python)
- **Engine**: Remotion (React, Puppeteer, FFmpeg)
- **Monitoring**: Flower
- **Database**: PostgreSQL & Redis
- **Infrastructure**: Podman/Docker Compose

---

## �️ Project Roadmap
- [ ] Multi-lingual transcript support
- [ ] Custom Font/Branding injection
- [ ] Auto-upload to TikTok/Insta/YouTube
- [ ] Web-based project creator (outside of Django Admin)

---

## 📄 License
Released under the **MIT License**. Feel free to fork, contribute, and use it for your massive content farms! 🚀
