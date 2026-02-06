# 🎬 AI Video Factory (Kontenio)

**Automated Vertical Video Factory** - A "Zero-Touch" video automation pipeline that transforms raw talking-head footage into high-retention vertical videos (9:16).

## 📋 Overview

This project creates professional split-screen vertical videos by:
1. **Transcribing** raw video audio using OpenAI Whisper
2. **Analyzing** transcripts with GPT-4o to generate contextual visual prompts
3. **Generating** AI images using DALL-E 3 or Stable Diffusion
4. **Rendering** the final video with Remotion (React-based video framework)

### Output Style
- **Split-Screen Layout**: Dynamic visuals (top) + talking head (bottom)
- **Glassmorphism Overlay**: Beautiful frosted-glass transcript display
- **Ken Burns Effect**: Subtle zoom animations on visuals
- **Professional Quality**: 1080x1920 @ 30fps, H.264 encoding

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+
- FFmpeg (for audio extraction)
- OpenAI API key

### Installation

```bash
# Clone and enter directory
cd kontenio

# Install Node dependencies (Remotion)
npm install

# Create Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install django openai-whisper openai

# Setup Django
python manage.py migrate

# Create symlink (required for Remotion to access media)
cd ..
ln -sfn $(pwd)/backend/media $(pwd)/public/media
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-key-here
```

---

## 🎯 Usage

### Basic Command

```bash
# Place your raw video in backend/media/raw/
# Then run:
cd backend
python manage.py make_video --input="your_video.mp4"
```

### Command Options

| Option | Description |
|--------|-------------|
| `--input` | **Required.** Filename in `media/raw/` directory |
| `--mock` | Use mock data (no API calls, for testing) |
| `--api` | Use OpenAI API for transcription (vs local Whisper) |
| `--style` | Style hint for visuals (default: "modern, cinematic, vibrant") |
| `--skip-images` | Skip image generation (use placeholder visuals) |
| `--skip-render` | Skip final render (only generate props.json) |

### Examples

```bash
# Full production pipeline
python manage.py make_video --input="my_content.mp4" --style="cyberpunk, neon"

# Quick test with mock data
python manage.py make_video --input="test.mp4" --mock

# Generate metadata only (no render)
python manage.py make_video --input="video.mp4" --skip-render
```

---

## 📁 Project Structure

```
./
├── backend/                    # Django Backend
│   ├── core/                   # Django Settings
│   ├── video/                  # Main App
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── make_video.py   # Pipeline Orchestrator
│   │   ├── ai_services.py      # Whisper, GPT, Image Gen
│   │   └── utils.py            # File utilities
│   └── media/
│       ├── raw/                # Input videos
│       ├── assets/             # Generated images
│       └── output/             # Final rendered videos
├── src/                        # Remotion Frontend
│   ├── compositions/
│   │   └── SplitScreen.tsx     # Main video component
│   └── Root.tsx                # Composition registry
├── public/
│   └── media/                  # Symlink → backend/media
└── remotion.config.ts          # Remotion configuration
```

---

## 🎨 Visual Style

### Video Specifications
- **Format**: 1080x1920 (9:16 vertical)
- **FPS**: 30
- **Codec**: H.264 (CRF 18)

### Layout
- **Top 50%**: AI-generated contextual visuals with Ken Burns zoom
- **Bottom 50%**: Original talking-head footage
- **Center Overlay**: Glassmorphism transcript box

### Glassmorphism Effect
```css
background: rgba(255, 255, 255, 0.15);
backdrop-filter: blur(16px);
border-radius: 30px;
border: 1px solid rgba(255, 255, 255, 0.25);
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
```

---

## 🛠️ Development

### Remotion Studio (Preview)

```bash
# Start Remotion Studio for live preview
npm run dev
```

Access at `http://localhost:3000`

### Render Video Manually

```bash
# Render with Remotion CLI
npx remotion render SplitScreen output.mp4 --props=public/media/render_props.json
```

### Django Development

```bash
cd backend
source venv/bin/activate
python manage.py runserver  # If you need the Django admin
```

---

## 📦 Dependencies

### Python
- Django 5.x
- openai-whisper (local transcription)
- openai (API client for GPT-4 and DALL-E)

### Node.js
- Remotion 4.x
- React 19
- TypeScript 5.x

### System
- FFmpeg (audio extraction)
- Node.js 18+
- Python 3.10+

---

## 🔧 Troubleshooting

### "Whisper not installed"
```bash
pip install openai-whisper
```

### "FFmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

### "Remotion not found"
```bash
npm install
```

### Symlink issues
```bash
# Remove and recreate symlink
rm -rf public/media
ln -sfn $(pwd)/backend/media $(pwd)/public/media
```

---

## 📄 License

UNLICENSED - Private Project

---

## 🤝 Contributing

This is a private automation tool. For questions or improvements, contact the project maintainer.
