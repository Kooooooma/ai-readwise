# AI-Readwise Project Rules

> **Note**: This is a 100% AI-generated project created by Google Antigravity.
> These rules help maintain consistency across different AI coding assistants.

## Project Overview

AI-Readwise is an intelligent reading tool that converts PDF eBooks to multilingual Markdown with:
- AI-powered translation (LangChain + OpenAI-compatible APIs)
- Chapter summarization with voice script generation
- TTS voice synthesis and podcast video production
- Real-time progress tracking with SSE
- Modern web interface (React + FastAPI)

## Tech Stack
- **Frontend**: TypeScript + React (Vite)
- **Backend**: Python 3
- **Package Manager**: npm (frontend), pip (backend)

## Python Environment
- **IMPORTANT**: Always use the `venv` virtual environment at `./venv/`
- Before installing any Python packages, activate venv first:
  ```bash
  # Windows
  .\venv\Scripts\activate
  
  # macOS/Linux
  source venv/bin/activate
  ```
- Install dependencies with: `pip install -r requirements.txt`
- When adding new packages, update `requirements.txt`

## LLM Configuration
- **Default Model**: Qwen Turbo (via OpenAI-compatible proxy)
- **Available Models**: qwen-turbo, gpt-4o-mini, gpt-4o
- **Provider**: Any OpenAI-compatible proxy service
- Translation and summarization features require valid LLM API configuration in `.env`

## Code Style

### Python
- Follow PEP 8 guidelines
- Use type hints where applicable
- Use f-strings for string formatting
- Keep functions focused and under 50 lines when possible
- Use descriptive variable names in English

### TypeScript/React
- Use functional components with hooks
- Prefer `const` over `let`
- Use TypeScript strict mode
- Keep components small and focused

## File Organization
- Backend code goes in `./backend/`
- Frontend code goes in `./frontend/`
- Static assets go in `./static/`
- Resources and data files go in `./resources/`

## General Guidelines
1. Be concise and professional
2. Always double-check file paths before writing
3. Write meaningful commit messages
4. Add comments for complex logic
5. Handle errors gracefully with proper error messages

## Project-Specific Notes

### PDF Extraction
- First run of `marker-pdf` downloads ~2GB of models
- Extraction uses multiprocess architecture for cancellation support
- Progress is persisted to `.extraction_progress.json` files

### Translation & Summarization
- Uses SSE (Server-Sent Events) for real-time progress
- Supports pause/resume with progress persistence
- All LLM calls go through LangChain abstraction layer

### Frontend Development
- Built with React 19 + Vite + TypeScript
- Uses Ant Design 6 for UI components
- State management with Zustand
- Markdown rendering with react-markdown

### Deployment
- Frontend builds to `frontend/dist/`
- FastAPI serves static files in production
- No separate web server needed

## Contribution Policy
- **This is a 100% AI-generated project**
- **No Pull Requests are accepted**
- Users should submit Issues for bugs and feature requests
- GitHub Repository: https://github.com/Kooooooma/ai-readwise
