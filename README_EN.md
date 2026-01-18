# AI-Readwise

<div align="center">

English | [简体中文](./README.md)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)

**AI-Powered Intelligent Reading Tool - Convert PDF eBooks to Multilingual Markdown with AI Translation, Chapter Summarization, and Podcast Generation**

[Quick Start](#-quick-start) • [Features](#-features)

</div>

---

## 📖 Project Overview

AI-Readwise is a full-stack intelligent reading solution designed for technical books, learning materials, and knowledge management. It converts traditional PDF eBooks into modern Markdown format and provides intelligent translation, content summarization, and voice podcast generation through large language models.

### 🎯 Problems Solved

- **Poor Reading Experience**: PDF format is inconvenient for online reading, annotation, and search
- **Language Barriers**: Quality technical books are mostly in English, lacking high-quality translations
- **Slow Knowledge Absorption**: Missing chapter summaries and key point extraction
- **Fragmented Learning**: Unable to fully utilize fragmented time like commuting for learning

### 💡 Technical Highlights

- ✅ **High-Quality PDF Extraction**: Based on marker-pdf, preserving formatting and images
- ✅ **AI Smart Translation**: LangChain + OpenAI with resume/pause capability
- ✅ **Real-time Progress Tracking**: SSE streaming with pause/resume support
- ✅ **Modular Architecture**: Frontend-backend separation, CLI tools independently usable
- ✅ **100% AI-Generated**: Entire project completed by AI assistant, showcasing AI programming capabilities

---

## ✨ Features

### Core Capabilities

| Module | Description | Tech Stack |
|--------|-------------|------------|
| 📚 **Web Reader** | Modern book management interface with chapter navigation, Markdown rendering, multilingual switching | React 19 + Ant Design 6 + TypeScript |
| ⚡ **Smart PDF Extraction** | High-quality PDF → Markdown conversion, preserving format, tables, images | marker-pdf + Python |
| 🌐 **AI Translation** | LLM-driven professional translation, supporting Chinese-English, resume capability, progress persistence | LangChain + OpenAI API |
| 🎯 **Chapter Summarization** | AI auto-extracts key points, conclusions, examples, generates podcast voice scripts | Qwen Turbo + Custom Prompts |
| 🎙️ **TTS Voice Synthesis** | Convert summaries to high-quality speech, supporting multiple languages and voices | edge-tts (Microsoft Speech) |
| 🎬 **Podcast Video Production** | Audio + background video composition, auto-generate podcast episodes | moviepy + FFmpeg |
| 🔄 **Real-time Progress** | SSE streaming, real-time display of PDF extraction and translation progress | FastAPI + Server-Sent Events |
| 💾 **Task Persistence** | Support resuming task state after page refresh and navigation | File system cache |

### Advanced Features

- **Multi-Model Support**: Compatible with OpenAI, Azure OpenAI, and any OpenAI-compatible API
- **Incremental Processing**: Translation and TTS support incremental generation, no reprocessing of completed content
- **Batch Operations**: One-click generation of summaries and MP3s for all chapters
- **CLI Toolchain**: Independent command-line tools for automated workflows
- **Async Architecture**: Multiprocess PDF extraction with true task cancellation

---

## 🎯 Use Cases

### 1️⃣ Technical Book Learning
- Convert English technical books to Markdown and translate to Chinese
- Quickly grasp core content through chapter summaries
- Listen to podcast versions during commute

### 2️⃣ Educational Content Creation
- Generate online course materials from PDF textbooks
- Auto-generate chapter summaries and learning points
- Produce accompanying audio courses

### 3️⃣ Knowledge Base Construction
- Convert enterprise training PDF materials to searchable Markdown
- Maintain multilingual versions synchronously
- Build internal knowledge management systems

### 4️⃣ Podcast Production
- Quickly convert text content to audio programs
- Compose video podcasts for social media distribution
- Batch generate series programs

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18 or higher
- **FFmpeg**: For audio/video processing (required for podcast features)
- **Operating System**: Windows / macOS / Linux

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Kooooooma/ai-readwise.git
cd ai-readwise
```

#### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note**: First run of `marker-pdf` will auto-download model files (~2GB), ensure stable network connection.

#### 3. Install FFmpeg (Optional)

```bash
# Windows (using Scoop)
scoop install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg

# macOS (using Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

#### 4. Configure LLM (Required for Translation)

Create `.env` file:

```env
# OpenAI API Configuration
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODELS=qwen-turbo,gpt-4o-mini,gpt-4o
LLM_DEFAULT_MODEL=qwen-turbo
```

**Supported LLM Providers**:
- Any OpenAI-compatible proxy service

#### 5. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 6. Start the Application

```bash
python app.py
```

Visit http://localhost:8000 to start using!

### Quick Usage

#### Adding Books

1. Create a book folder in `resources/` directory (e.g., `my-book/`)
2. Create `description.md` in that folder:

```yaml
title: Shoe Dog
description: A Memoir by the Creator of Nike
file: shoe-dog.pdf
```

3. Place the PDF file in the same folder

#### Web Interface Usage

1. **Home Bookshelf**: Browse all added books
2. **Extract Content**: Open book → Click "Extract PDF Content" → Wait for completion
3. **AI Translation**: Select target language → Select model → Start translation
4. **Chapter Summary**: Click "Generate Summary" on the right side of chapter → View AI summary and podcast script
5. **Voice Synthesis**: Click "Generate MP3" → Play online

#### CLI Tools Usage

```bash
# PDF to Markdown
python pdf_to_markdown.py book.pdf -o book.md

# Split chapters by top-level headings
python split_markdown.py book.md -o chapters/

# Batch generate voice (incremental mode + auto merge)
python text_to_speech.py -d ./scripts --merge -o podcast.mp3

# Compose video podcast
python merge_audio_video.py podcast.mp3 background.mp4 -o output.mp4
```

---

### Technology Stack

#### Backend Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.100+ | Async web framework for REST API and SSE |
| **Uvicorn** | 0.20+ | ASGI server for production deployment |
| **marker-pdf** | latest | High-quality PDF → Markdown conversion |
| **LangChain** | 0.1+ | LLM application framework, wrapping OpenAI calls |
| **edge-tts** | latest | Microsoft Edge free TTS service |
| **moviepy** | 1.0+ | Python video editing library |
| **pydub** | 0.25+ | Audio processing library |

#### Frontend Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 19 | UI framework with latest Hooks API |
| **TypeScript** | 5.9+ | Type-safe JavaScript |
| **Vite** | 7.2+ | Fast build tool and dev server |
| **Ant Design** | 6.1+ | Enterprise-level UI component library |
| **React Router** | 7.12+ | Client-side routing |
| **Zustand** | 5.0+ | Lightweight state management |
| **react-markdown** | 10.1+ | Markdown rendering component |

### Directory Structure

```
ai-readwise/
├── app.py                      # FastAPI application entry
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (need to create)
│
├── backend/                    # Backend service modules
│   ├── api.py                 # REST API and SSE routes
│   ├── models.py              # Pydantic data models
│   ├── services.py            # Book and translation services
│   ├── summary_service.py     # Chapter summary service
│   ├── marker_extract.py      # PDF extraction core logic
│   ├── extract_worker.py      # Multiprocess extraction worker
│   └── translation_service.py # LLM translation service
│
├── frontend/                   # React frontend app
│   ├── src/
│   │   ├── pages/             # Page components
│   │   │   ├── HomePage.tsx   # Bookshelf home
│   │   │   └── BookDetailPage.tsx  # Book details
│   │   ├── components/        # UI components
│   │   │   ├── BookCard.tsx
│   │   │   ├── ChapterList.tsx
│   │   │   ├── ExtractPanel.tsx
│   │   │   ├── TranslationPanel.tsx
│   │   │   ├── BatchSummaryPanel.tsx
│   │   │   └── ...
│   │   ├── api/               # API client
│   │   │   └── client.ts
│   │   └── store/             # Zustand state
│   │       └── bookStore.ts
│   ├── dist/                  # Build artifacts (deployment)
│   └── package.json           # Node.js dependencies
│
├── resources/                  # Book resources directory
│   └── {book-id}/             # Book folder
│       ├── description.md     # Book metadata
│       ├── {filename}.pdf     # Original PDF file
│       ├── {book-id}.md       # Extracted full Markdown
│       ├── {book-id}/         # Chapter directory
│       │   ├── 00_preface.md
│       │   ├── 01_chapter1.md
│       │   └── ...
│       ├── {book-id}_zh/      # Chinese translation
│       ├── {book-id}_en/      # English version (if original is other language)
│       └── summaries/         # Chapter summaries
│           ├── *.json         # Summary JSON
│           └── *.mp3          # TTS audio
│
├── static/                     # Static assets
│   └── images/                # Book covers etc.
│
├── pdf_to_markdown.py         # CLI: PDF → Markdown
├── split_markdown.py          # CLI: Markdown splitting
├── text_to_speech.py          # CLI: Text to speech
├── merge_audio_video.py       # CLI: Audio/video composition
└── merge_markdown_to_html.py # CLI: Markdown → HTML
```

---

## 🛠️ Development Guide

### Local Development

#### Frontend Development

```bash
cd frontend
npm install
npm run dev        # Dev server http://localhost:5173
npm run build      # Production build
npx tsc --noEmit   # TypeScript type checking
```

**Development Tools**:
- Google Antigravity
- Prettier
- ESLint auto-formatting
- TypeScript strict mode

#### Backend Development

```bash
# Start dev server (auto-reload)
python app.py

# Python syntax check
python -m py_compile backend/*.py

# View API docs
# Visit http://localhost:8000/docs after starting
```

### API Overview

#### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/books` | Get all books list |
| GET | `/api/books/{id}` | Get book details |
| GET | `/api/books/{id}/chapters` | Get chapters list (default language) |
| GET | `/api/books/{id}/chapters/{lang}` | Get chapters for specific language |
| GET | `/api/books/{id}/chapter/{filename}` | Get chapter content |
| GET | `/api/books/{id}/languages` | Get available language info |
| GET | `/api/books/{id}/source` | Get source Markdown |
| PUT | `/api/books/{id}/source` | Update source Markdown |
| POST | `/api/books/{id}/resplit` | Re-split chapters |
| GET | `/api/translation/models` | Get available LLM models |

#### SSE Streaming Endpoints

| Path | Description |
|------|-------------|
| `/api/books/{id}/extract?cancel=false` | PDF extraction progress stream |
| `/api/books/{id}/translate?lang={lang}&model={model}` | Translation progress stream |

**SSE Event Example**:

```javascript
// Extraction progress event
{
  "status": "processing",  // pending/processing/completed/failed/cancelled
  "progress": 45,          // 0-100
  "message": "Extracting page 3/7...",
  "current_step": "extraction",
  "total_chapters": 0
}

// Translation progress event
{
  "status": "processing",
  "progress": 60,
  "message": "Translating chapter 3/5...",
  "current_chapter": 3,
  "total_chapters": 5
}
```

### CLI Tools Details

#### pdf_to_markdown.py

```bash
python pdf_to_markdown.py <input.pdf> -o <output.md>

# Example
python pdf_to_markdown.py books/clean-code.pdf -o clean-code.md
```

**Parameters**:
- `input`: PDF file path
- `-o, --output`: Output Markdown file path

#### split_markdown.py

```bash
python split_markdown.py <input.md> -o <output_dir/>

# Example
python split_markdown.py clean-code.md -o chapters/
```

**Function**: Split by top-level headings (`# Title`) into multiple files

#### text_to_speech.py

```bash
python text_to_speech.py -d <scripts_dir/> [--merge] [-o output.mp3]

# Example: Incremental generation + merge
python text_to_speech.py -d ./scripts --merge -o podcast.mp3
```

**Parameters**:
- `-d, --dir`: Directory containing .txt scripts
- `--merge`: Auto-merge all MP3s into single file
- `-o, --output`: Merged output filename

**Features**:
- Auto-skip already generated MP3s (incremental mode)
- Support multiple voices and languages
- Parallel processing for speed

#### merge_audio_video.py

```bash
python merge_audio_video.py <audio.mp3> <video.mp4> -o <output.mp4>

# Example
python merge_audio_video.py podcast.mp3 background.mp4 -o final.mp4
```

**Function**: Compose audio and video into podcast video

### Debugging Tips

#### Frontend Debugging

- Use React DevTools to view component state
- Enable request logging in `api/client.ts`
- Check Network panel for EventStream (SSE)

#### Backend Debugging

- FastAPI auto-generates Swagger docs: `/docs`
- Check console logs for service execution flow
- Inspect `resources/{book-id}/.extraction_progress.json` for task status

---

## 🤝 Contributing

### Important Notice

> [!IMPORTANT]
> **This Project is 100% AI-Generated**
> 
> AI-Readwise is a project entirely generated by an AI programming assistant (Google Antigravity), aiming to showcase AI capabilities in full-stack development.
>
> **Therefore, we do NOT accept Pull Requests (PRs)**.

### How to Provide Feedback

We welcome your participation via **GitHub Issues**:

#### 🐛 Bug Reports

Use the **Bug Report** template, please include:
- Detailed reproduction steps
- Expected behavior vs actual behavior
- System environment (OS, Python version, Node.js version)
- Error logs or screenshots

#### 💡 Feature Requests

Use the **Feature Request** template, please describe:
- Use case for the feature
- Expected implementation effect
- Impact on existing features

#### ❓ Usage Questions

Use the **Question** label, we'll respond as soon as possible.

### AI Implementation Process

Submitted issues will be handled collaboratively by project maintainers and AI assistant:
1. Evaluate feasibility and priority of requirements
2. AI generates implementation plan
3. Human reviews code quality
4. Release updates

---

## 📊 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Kooooooma/ai-readwise&type=Date)](https://star-history.com/#Kooooooma/ai-readwise&Date)

If this project helps you, please give us a ⭐️!

---

## 📄 License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

### License Summary

✅ **Permissions**:
- Commercial use
- Modification
- Distribution
- Patent use
- Private use

❌ **Conditions**:
- State original author and license
- Mark modifications
- Include original license text

❌ **Limitations**:
- Use of project trademarks
- Warranty provided

For detailed terms, see the [LICENSE](./LICENSE) file.

---

## 🙏 Acknowledgments

### Open Source Projects

- [marker-pdf](https://github.com/VikParuchuri/marker) - Excellent PDF extraction tool
- [LangChain](https://github.com/langchain-ai/langchain) - Powerful LLM application framework
- [edge-tts](https://github.com/rany2/edge-tts) - Python implementation of Microsoft Edge TTS
- [FastAPI](https://github.com/tiangolo/fastapi) - Modern Python web framework
- [Ant Design](https://github.com/ant-design/ant-design) - Excellent React UI library

### AI-Driven Development

This project was generated by **Google Antigravity** AI programming assistant, demonstrating AI capabilities in complex software engineering.

---

## 📮 Contact

- **Issues**: [GitHub Issues](https://github.com/Kooooooma/ai-readwise/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Kooooooma/ai-readwise/discussions)

---

<div align="center">

**⭐️ If you find it useful, please give it a Star! ⭐️**

Made with 🤖 by AI • Curated with ❤️ by Human

[⬆️ Back to Top](#ai-readwise)

</div>
