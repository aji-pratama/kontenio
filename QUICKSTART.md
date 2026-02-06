# AI Video Factory - Quick Start Guide

## 🚀 Cara Pakai Mock Mode (Testing Tanpa API)

### 1. Persiapan
Pastikan server jalan:
```bash
make dev
```

Ini akan menjalankan:
- Django Admin di http://localhost:9000
- Remotion Studio di http://localhost:3000

### 2. Upload Video
1. Buka http://localhost:9000/admin
2. Login dengan credentials admin kamu
3. Klik **Video projects** → **Add video project**
4. Isi form:
   - **Title**: "Test Video Mock"
   - **Raw video**: Upload file video (.mp4 atau .mov)
   - **Transcription provider**: **Mock (Testing)**
   - **LLM provider**: **Mock (Testing)**
   - **Image provider**: **Mock (Testing)**
   - **Style hint**: "cyberpunk" (atau "modern", "cinematic", dll)
5. Klik **Save**

### 3. Process Video
1. Kembali ke list **Video projects**
2. **Centang** project yang baru kamu buat
3. Dari dropdown **Action**, pilih **🧪 Process (Mock)**
4. Klik **Go**

Tunggu beberapa detik. Django akan:
- ✅ Generate mock transcript (10 segments)
- ✅ Generate mock visual prompts (6 prompts)
- ✅ Generate mock images (placeholder)
- ✅ Create props.json file
- ✅ Render video dengan Remotion

### 4. Lihat Hasil

**OPSI A: Di Django Admin**
1. Refresh halaman
2. Klik nama project untuk lihat detail
3. Scroll ke bawah, lihat:
   - **Transcript data**: JSON berisi 10 segments
   - **Visual prompts data**: JSON berisi 6 prompts
   - **Visual assets**: Inline tabel dengan preview gambar
   - **Props file**: Link untuk download JSON
   - **Output video**: Video player dengan hasil render

**OPSI B: Di Remotion Studio** 
1. Buka http://localhost:3000
2. Klik composition **"SplitScreen"**
3. Props akan otomatis dimuat dari `public/media/render_props.json`
4. Kamu bisa lihat preview real-time:
   - Panel atas: Gambar AI yang muncul sesuai timing
   - Panel bawah: Video asli
   - Overlay: Subtitle glassmorphism

**OPSI C: Download Video**
1. Kembali ke Django Admin
2. Di list projects, lihat kolom **Actions**
3. Klik tombol **⬇ Download** (hijau) untuk download MP4

### 5. Troubleshooting

**Error: "ffmpeg not found"**
```bash
brew install ffmpeg
# Lalu restart make dev
```

**Error: "remotion not found"**
```bash
npm install
# Pastikan package.json punya remotion
```

**Tidak ada output video tapi status "Completed"**
- Cek error message di kolom Actions (hover untuk lihat detail)
- Kemungkinan render gagal tapi data (transcript, images) sudah jadi
- Bisa lihat hasil di Remotion Studio meskipun render gagal

**Props file tidak muncul di Remotion**
```bash
# Cek apakah symlink sudah dibuat
ls -la public/media
# Kalau belum, jalankan:
make setup
```

### 6. Mode Production (Pakai AI Asli)

Sama seperti di atas, tapi:
- **Providers**: Pilih OpenAI atau Gemini (bukan Mock)
- Pastikan API key sudah di-set di `.env`:
  ```bash
  OPENAI_API_KEY=sk-xxx
  GEMINI_API_KEY=xxx
  ```
- Pilih action **🚀 Process (Production)**

---

## 📁 File Struktur

```
backend/media/
  ├── raw/          # Video asli yang kamu upload
  ├── assets/       # Gambar hasil AI generation
  ├── props/        # JSON props untuk Remotion
  └── output/       # Video final hasil render

public/media/       # Symlink ke backend/media
  └── render_props.json  # Props yang dibaca Remotion Studio
```

## 🎨 Style Hints

Kamu bisa pakai style berikut di field **Style hint**:
- `modern` - Clean, minimalist, high-end commercial
- `cyberpunk` - Neon, futuristic, high contrast
- `animation` - 2D character style, vibrant colors
- `3d_render` - Octane render, realistic, cinematic
- `illustration` - Hand-drawn digital art
- `motion` - Kinetic typography, abstract shapes
- `cinematic` - Hollywood movie look, anamorphic

Style ini mempengaruhi bagaimana AI men-generate visual prompts dan gambar.
