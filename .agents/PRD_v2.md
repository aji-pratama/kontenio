# Video Automation Agent Context: Dynamic Split-Screen Layout

# Objective:
Generate a high-engagement, automated vertical video (9:16) for an AI SaaS platform.
The agent must handle multi-layer composition, random event-based layout switching, 
and high-end visual styling without the overhead of a headless browser.

# Component Specifications:

1. Primary Layers:
   - Base Layer (Bottom): "talking_head.mp4" 
     - Context: Spokesperson/Influencer speaking directly to the camera.
   - Secondary Layer (Top): "b-roll_assets"
     - Source: Generative AI (Nano Banana), static memes, illustrations, or stock footage.
     - Dynamic Effects: Subtle Ken Burns effect (slow zoom), lateral pans, or emoji overlays.

2. Central Transcript Overlay (Apple Glass Aesthetic):
   - Style: Glassmorphism effect.
   - Implementation: Semi-transparent frosted-glass container (low opacity, blurred background).
   - Typography: San Francisco or Inter font, bold, centered, high-contrast white text.
   - Sync: Dynamic word-level subtitles synchronized via Whisper AI (SRT/VTT).

3. Behavioral Logic (Period-Based Randomization):
   - The Agent must segment the timeline into random intervals (e.g., 3-7 seconds).
   - Random Layout Triggers:
     - [Split Mode]: Standard 50/50 vertical split.
     - [Focus Mode A]: Bottom video scales to 100% (Fullscreen) while maintaining background sync.
     - [Focus Mode B]: Top asset scales to 100% (Fullscreen) to emphasize visual metaphors or memes.

# Technical Requirements:
- Engine: Python-based (MoviePy/FFmpeg) for high-performance server-side rendering.
- Scalability: Compatible with Django/Celery for asynchronous task processing.
- Optimization: Use 'ultrafast' encoding presets to minimize CPU latency and maximize throughput.
- Flexibility: The system must be "Pattern-First"—randomized within predefined logical constraints.

---

User adjustment --> admin.py

# PRD: AI-Powered Viral Video Automator
# Version: 1.0 (Feb 2026)
# Tech Stack: Django, Celery, PostgreSQL (pgvector), MoviePy, Whisper, Nano Banana

---

## 1. DATA MODELS (The Logic Foundation)

### A. Project Model
- user: ForeignKey(User)
- title: CharField
- raw_video: FileField (Original user upload)
- processed_video_1080p: FileField (Optimized version for rendering)
- status: Choice(Draft, Analyzing, Ready_to_Edit, Rendering, Completed, Failed)
- global_style: CharField (e.g., "3D Tactile", "Flat Minimalist", "Cyberpunk")
- created_at: DateTime

### B. VideoSegment Model (The "Table" Data)
- project: ForeignKey(Project)
- order: PositiveIntegerField (Sequence of the clip)
- start_time: FloatField (seconds)
- end_time: FloatField (seconds)
- transcript: TextField (Editable by user)
- asset_type: Choice(AI_Image, User_Upload, Video_Clip, Meme, Emoji)
- asset_file: FileField (The overlay asset path)
- layout_event: Choice(Standard_Split, Full_Bottom, Full_Top)
- animation_type: Choice(Ken_Burns, Side_Slide, Static)

---

## 2. SYSTEM WORKFLOW (Step-by-Step)

### Phase 1: Ingestion & Analysis (The Hook)
1. User uploads "talking head" video.
2. **Task 1 (Celery):** Transcribe via OpenAI Whisper.
3. **Task 2 (Python Logic):** Parse Whisper JSON into segments (1-5s intervals) based on natural pauses or sentence ends.
4. **Task 3:** Initialize `VideoSegment` entries and set project status to 'Ready to Edit'.

### Phase 2: User Enrichment (The Review Table)
1. User enters the Dashboard "Review Table".
2. **Manual Override:** User refines the transcript text if Whisper misinterprets slang.
3. **Asset Assignment:**
   - **Manual:** User uploads local PNG/MP4.
   - **Auto-Generate (Nano Banana):** One-click generation. System feeds `transcript` + `global_style` -> Nano Banana API -> saves result to `asset_file`.

### Phase 3: Rendering Engine (The Muscle)
1. User triggers "Generate Final Video".
2. **Task 4 (Celery - Heavy Duty):**
   - Initialize MoviePy `CompositeVideoClip` with a high-quality background.
   - Loop through `VideoSegment` records.
   - Execute `subclip(start, end)` with designated `layout_event`.
   - **Layering Subtitles:** Burn-in "Apple Glass" style text (frosted glass box + Inter Bold font).
3. **Task 5:** Concatenate all processed segments.
4. **Task 6:** Final export using FFmpeg `libx264` with `ultrafast` preset for maximum throughput.

---

## 3. VISUAL STYLE SPECIFICATIONS (Apple Glass & "Timbul" Aesthetic)

### A. Subtitle Container (The Middle Layer)
- **Background:** Semi-transparent white/gray box (Opacity: 0.15) with a 1px white border (Opacity: 0.3).
- **Glassmorphism:** Apply a Gaussian Blur background filter behind the text container to simulate frosted glass.
- **Shadow:** Hard, sharp shadow (Offset: 4px, Color: Black, Opacity: 0.5) to achieve the "Timbul" (3D tactile) look.

### B. Dynamic Motion (Top Layer)
- **Image Assets:** Apply a dynamic **Ken Burns Effect** (Slow zoom-in from 1.0x to 1.1x) to keep static AI images engaging.
- **Transitions:** Use subtle 0.2s crossfades between layout switches to prevent visual jarring.

---

## 4. SCALABILITY & PERFORMANCE (The SaaS Builder Strategy)

- **Worker Concurrency:** Optimize Celery workers based on CPU core count (e.g., 1 worker per 2 vCPUs).
- **Resource Management:** Auto-purge `raw_video` files after 48 hours post-completion to optimize disk space.
- **GPU Acceleration (Optional):** If scaling, move to `h264_nvenc` (NVIDIA) or AWS Lambda for parallelizing segments.

---

## 5. MVP SUCCESS METRICS
- **Latency:** 60-second video rendered in < 180 seconds.
- **Accuracy:** > 95% Transcript accuracy using Whisper Large-v3.
- **Stability:** 0% "Headless Browser Crash" errors (Eliminating Remotion dependency).
