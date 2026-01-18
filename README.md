# AI-Readwise

<div align="center">

[English](./README_EN.md) | 简体中文

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)

**AI 驱动的智能阅读工具 - 将 PDF 电子书转换为多语言 Markdown，支持 AI 翻译、章节总结和播客制作**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [在线演示](#) • [文档](#-开发指南)

</div>

---

## 📖 项目概述

AI-Readwise 是一个全栈智能阅读解决方案，专为技术书籍、学习资料和知识管理而设计。它将传统的 PDF 电子书转换为现代化的 Markdown 格式，并通过大语言模型提供智能翻译、内容总结和语音播客生成功能。

### 🎯 解决的问题

- **阅读体验差**：PDF 格式不便于在线阅读、批注和搜索
- **语言障碍**：优质技术书籍多为英文,缺乏高质量中文翻译
- **知识吸收慢**：缺少章节总结和关键点提炼
- **碎片化学习**：无法充分利用通勤等碎片时间学习

### 💡 技术亮点

- ✅ **高质量 PDF 提取**：基于 marker-pdf,保留格式和图片
- ✅ **AI 智能翻译**：LangChain + OpenAI,支持断点续传
- ✅ **实时进度追踪**：SSE 流式传输,支持暂停/继续
- ✅ **模块化架构**：前后端分离,CLI 工具独立可用
- ✅ **100% AI 生成**：整个项目由 AI 助手完成,展示 AI 编程能力

---

## ✨ 功能特性

### 核心功能

| 功能模块 | 描述 | 技术栈 |
|---------|------|--------|
| 📚 **Web 阅读器** | 现代化书籍管理界面，支持章节导航、Markdown 渲染、多语言切换 | React 19 + Ant Design 6 + TypeScript |
| ⚡ **PDF 智能提取** | 高质量 PDF → Markdown 转换，保留格式、表格、图片 | marker-pdf + Python |
| 🌐 **AI 翻译** | LLM 驱动的专业级翻译，支持中英双语，断点续传，进度持久化 | LangChain + OpenAI API |
| 🎯 **章节总结** | AI 自动提取关键点、结论、示例，生成播客语音脚本 | Qwen Turbo + 自定义 Prompt |
| 🎙️ **TTS 语音合成** | 将总结内容转换为高质量语音，支持多语言、多音色 | edge-tts (微软语音) |
| 🎬 **播客视频制作** | 音频 + 背景视频合成，自动生成播客节目 | moviepy + FFmpeg |
| 🔄 **实时进度追踪** | SSE 流式传输，实时显示 PDF 提取、翻译进度 | FastAPI + Server-Sent Events |
| 💾 **任务持久化** | 支持页面刷新、导航后恢复任务状态 | 文件系统缓存 |

### 高级特性

- **多模型支持**：兼容 OpenAI、Azure OpenAI 及任何 OpenAI 兼容 API
- **增量处理**：翻译和 TTS 支持增量生成，已完成内容不重复处理
- **批量操作**：一键生成全书所有章节的总结和 MP3
- **CLI 工具链**：独立命令行工具，适合自动化工作流
- **异步架构**：多进程 PDF 提取，支持真正的任务取消

---

## 🎯 应用场景

### 1️⃣ 技术书籍学习
- 将英文技术书籍转换为 Markdown 并翻译为中文
- 通过章节总结快速把握核心内容
- 利用通勤时间收听播客版本

### 2️⃣ 教育内容创作
- 从 PDF 教材生成在线课程资料
- 自动生成章节摘要和学习要点
- 制作配套音频课程

### 3️⃣ 知识库构建
- 将企业培训资料 PDF 转换为可搜索的 Markdown
- 多语言版本同步维护
- 构建内部知识管理系统

### 4️⃣ 播客节目制作
- 快速将文字内容转换为音频节目
- 合成视频播客用于社交媒体分发
- 批量生成系列节目

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **Node.js**: 18 或更高版本
- **FFmpeg**: 用于音视频处理 (播客功能需要)
- **操作系统**: Windows / macOS / Linux

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/Kooooooma/ai-readwise.git
cd ai-readwise
```

#### 2. 安装 Python 依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv

# 激活虚拟环境
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> **注意**: 首次运行 `marker-pdf` 会自动下载模型文件 (~2GB),请确保网络畅通。

#### 3. 安装 FFmpeg (可选)

```bash
# Windows (使用 Scoop)
scoop install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS (使用 Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

#### 4. 配置 LLM (翻译功能需要)

创建 `.env` 文件：

```env
# OpenAI API 配置
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODELS=qwen-turbo,gpt-4o-mini,gpt-4o
LLM_DEFAULT_MODEL=qwen-turbo
```

**支持的 LLM 提供商**:
- 任何 OpenAI 兼容的代理服务

#### 5. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 6. 启动应用

```bash
python app.py
```

访问 http://localhost:8000 开始使用！

### 快速使用

#### 添加书籍

1. 在 `resources/` 目录下创建书籍文件夹 (如 `my-book/`)
2. 在该文件夹创建 `description.md`:

```yaml
title: 鞋狗
description: 耐克创始人菲尔·奈特亲笔自传
file: shoe-dog.pdf
```

3. 将 PDF 文件放入同一文件夹

#### Web 界面使用

1. **首页书架**: 浏览所有已添加的书籍
2. **提取内容**: 打开书籍 → 点击「提取 PDF 内容」→ 等待提取完成
3. **AI 翻译**: 选择目标语言 → 选择模型 → 开始翻译
4. **章节总结**: 在章节右侧点击「生成总结」→ 查看 AI 总结和播客脚本
5. **语音合成**: 点击「生成 MP3」→ 在线播放

#### CLI 工具使用

```bash
# PDF 转 Markdown
python pdf_to_markdown.py book.pdf -o book.md

# 按一级标题拆分章节
python split_markdown.py book.md -o chapters/

# 批量生成语音 (增量模式 + 自动合并)
python text_to_speech.py -d ./scripts --merge -o podcast.mp3

# 合成视频播客
python merge_audio_video.py podcast.mp3 background.mp4 -o output.mp4
```

---

### 技术栈

#### 后端技术

| 技术 | 版本 | 用途 |
|-----|------|-----|
| **FastAPI** | 0.100+ | 异步 Web 框架,提供 REST API 和 SSE |
| **Uvicorn** | 0.20+ | ASGI 服务器,生产环境部署 |
| **marker-pdf** | latest | 高质量 PDF → Markdown 转换 |
| **LangChain** | 0.1+ | LLM 应用框架,封装 OpenAI 调用 |
| **edge-tts** | latest | 微软 Edge 免费 TTS 服务 |
| **moviepy** | 1.0+ | Python 视频编辑库 |
| **pydub** | 0.25+ | 音频处理库 |

#### 前端技术

| 技术 | 版本 | 用途 |
|-----|------|-----|
| **React** | 19 | UI 框架,采用最新 Hooks API |
| **TypeScript** | 5.9+ | 类型安全的 JavaScript |
| **Vite** | 7.2+ | 快速构建工具和开发服务器 |
| **Ant Design** | 6.1+ | 企业级 UI 组件库 |
| **React Router** | 7.12+ | 客户端路由 |
| **Zustand** | 5.0+ | 轻量级状态管理 |
| **react-markdown** | 10.1+ | Markdown 渲染组件 |

### 目录结构

```
ai-readwise/
├── app.py                      # FastAPI 应用入口
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量 (需自建)
│
├── backend/                    # 后端服务模块
│   ├── api.py                 # REST API 和 SSE 路由
│   ├── models.py              # Pydantic 数据模型
│   ├── services.py            # 书籍和翻译服务
│   ├── summary_service.py     # 章节总结服务
│   ├── marker_extract.py      # PDF 提取核心逻辑
│   ├── extract_worker.py      # 多进程提取 Worker
│   └── translation_service.py # LLM 翻译服务
│
├── frontend/                   # React 前端应用
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   │   ├── HomePage.tsx   # 书架首页
│   │   │   └── BookDetailPage.tsx  # 书籍详情
│   │   ├── components/        # UI 组件
│   │   │   ├── BookCard.tsx
│   │   │   ├── ChapterList.tsx
│   │   │   ├── ExtractPanel.tsx
│   │   │   ├── TranslationPanel.tsx
│   │   │   ├── BatchSummaryPanel.tsx
│   │   │   └── ...
│   │   ├── api/               # API 客户端
│   │   │   └── client.ts
│   │   └── store/             # Zustand 状态
│   │       └── bookStore.ts
│   ├── dist/                  # 构建产物 (部署)
│   └── package.json           # Node.js 依赖
│
├── resources/                  # 书籍资源目录
│   └── {book-id}/             # 书籍文件夹
│       ├── description.md     # 书籍元数据
│       ├── {filename}.pdf     # PDF 原文件
│       ├── {book-id}.md       # 提取的完整 Markdown
│       ├── {book-id}/         # 章节目录
│       │   ├── 00_preface.md
│       │   ├── 01_chapter1.md
│       │   └── ...
│       ├── {book-id}_zh/      # 中文翻译版
│       ├── {book-id}_en/      # 英文版 (如原文为其他语言)
│       └── summaries/         # 章节总结
│           ├── *.json         # 总结 JSON
│           └── *.mp3          # TTS 语音
│
├── static/                     # 静态资源
│   └── images/                # 书籍封面等
│
├── pdf_to_markdown.py         # CLI: PDF → Markdown
├── split_markdown.py          # CLI: Markdown 拆分
├── text_to_speech.py          # CLI: 文本转语音
├── merge_audio_video.py       # CLI: 音视频合成
└── merge_markdown_to_html.py # CLI: Markdown → HTML
```

---

## 🛠️ 开发指南

### 本地开发

#### 前端开发

```bash
cd frontend
npm install
npm run dev        # 开发服务器 http://localhost:5173
npm run build      # 生产构建
npx tsc --noEmit   # TypeScript 类型检查
```

**开发工具**:
- Google Antigravity
- Prettier
- ESLint 自动格式化
- TypeScript 严格模式

#### 后端开发

```bash
# 启动开发服务器 (自动重载)
python app.py

# Python 语法检查
python -m py_compile backend/*.py

# 查看 API 文档
# 启动后访问 http://localhost:8000/docs
```

### API 概览

#### REST 端点

| 方法 | 路径 | 描述 |
|-----|------|-----|
| GET | `/api/books` | 获取所有书籍列表 |
| GET | `/api/books/{id}` | 获取书籍详情 |
| GET | `/api/books/{id}/chapters` | 获取章节列表 (默认语言) |
| GET | `/api/books/{id}/chapters/{lang}` | 获取指定语言的章节列表 |
| GET | `/api/books/{id}/chapter/{filename}` | 获取章节内容 |
| GET | `/api/books/{id}/languages` | 获取可用语言信息 |
| GET | `/api/books/{id}/source` | 获取源 Markdown |
| PUT | `/api/books/{id}/source` | 更新源 Markdown |
| POST | `/api/books/{id}/resplit` | 重新拆分章节 |
| GET | `/api/translation/models` | 获取可用 LLM 模型 |

#### SSE 流式端点

| 路径 | 描述 |
|-----|-----|
| `/api/books/{id}/extract?cancel=false` | PDF 提取进度流 |
| `/api/books/{id}/translate?lang={lang}&model={model}` | 翻译进度流 |

**SSE 事件示例**:

```javascript
// 提取进度事件
{
  "status": "processing",  // pending/processing/completed/failed/cancelled
  "progress": 45,          // 0-100
  "message": "正在提取第 3/7 页...",
  "current_step": "extraction",
  "total_chapters": 0
}

// 翻译进度事件
{
  "status": "processing",
  "progress": 60,
  "message": "正在翻译第 3/5 章...",
  "current_chapter": 3,
  "total_chapters": 5
}
```

### CLI 工具详解

#### pdf_to_markdown.py

```bash
python pdf_to_markdown.py <input.pdf> -o <output.md>

# 示例
python pdf_to_markdown.py books/clean-code.pdf -o clean-code.md
```

**参数**:
- `input`: PDF 文件路径
- `-o, --output`: 输出 Markdown 文件路径

#### split_markdown.py

```bash
python split_markdown.py <input.md> -o <output_dir/>

# 示例
python split_markdown.py clean-code.md -o chapters/
```

**功能**: 按一级标题 (`# Title`) 拆分为多个文件

#### text_to_speech.py

```bash
python text_to_speech.py -d <scripts_dir/> [--merge] [-o output.mp3]

# 示例: 增量生成 + 合并
python text_to_speech.py -d ./scripts --merge -o podcast.mp3
```

**参数**:
- `-d, --dir`: 包含 .txt 脚本的目录
- `--merge`: 自动合并所有 MP3 为单个文件
- `-o, --output`: 合并后的输出文件名

**特性**:
- 自动跳过已生成的 MP3 (增量模式)
- 支持多种语音和语言
- 并行处理提升速度

#### merge_audio_video.py

```bash
python merge_audio_video.py <audio.mp3> <video.mp4> -o <output.mp4>

# 示例
python merge_audio_video.py podcast.mp3 background.mp4 -o final.mp4
```

**功能**: 将音频和视频合成为播客视频

### 调试技巧

#### 前端调试

- 使用 React DevTools 查看组件状态
- 在 `api/client.ts` 中启用请求日志
- 查看 Network 面板的 EventStream (SSE)

#### 后端调试

- FastAPI 自动生成 Swagger 文档: `/docs`
- 查看控制台日志了解服务执行流程
- 检查 `resources/{book-id}/.extraction_progress.json` 了解任务状态

---

## 🤝 如何参与贡献

### 重要声明

> [!IMPORTANT]
> **本项目 100% 由 AI 生成**
> 
> AI-Readwise 是一个完全由 AI 编程助手 (Google Antigravity) 生成的项目,旨在展示 AI 在全栈开发中的能力。
>
> **因此,我们不接受 Pull Requests (PR)**。

### 如何反馈问题和需求

我们非常欢迎您通过 **GitHub Issues** 参与项目:

#### 🐛 报告 Bug

使用 **Bug Report** 模板,请包含:
- 详细的复现步骤
- 预期行为 vs 实际行为
- 系统环境 (OS, Python 版本, Node.js 版本)
- 错误日志或截图

#### 💡 功能建议

使用 **Feature Request** 模板,请描述:
- 功能的使用场景
- 期望的实现效果
- 对现有功能的影响

#### ❓ 使用问题

使用 **Question** 标签,我们会尽快回复。

### AI 实现流程

提交的 Issue 将由项目维护者与 AI 助手协作处理:
1. 评估需求的合理性和优先级
2. 由 AI 生成实现方案
3. 人工审核代码质量
4. 发布更新

---

## 📊 Star History

[![Star History Chart](https://api.star-history.com/svg?repos={owner}/{repo}&type=Date)](https://star-history.com/#/{owner}/{repo}&Date)

如果这个项目对您有帮助,请给我们一个 ⭐️!

---

## 📄 开源协议

本项目采用 [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) 开源协议。

### 许可摘要

✅ **允许**:
- 商业使用
- 修改代码
- 分发
- 专利使用
- 私人使用

❌ **要求**:
- 声明原作者和许可证
- 标注修改内容
- 包含原始许可证文本

❌ **禁止**:
- 使用项目商标
- 提供担保

详细条款请查看 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

### 开源项目

- [marker-pdf](https://github.com/VikParuchuri/marker) - 出色的 PDF 提取工具
- [LangChain](https://github.com/langchain-ai/langchain) - 强大的 LLM 应用框架
- [edge-tts](https://github.com/rany2/edge-tts) - 微软 Edge TTS 的 Python 实现
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代 Python Web 框架
- [Ant Design](https://github.com/ant-design/ant-design) - 优秀的 React UI 库

### AI 驱动开发

本项目由 **Google Antigravity** AI 编程助手生成,展示了 AI 在复杂软件工程中的能力。

---

## 📮 联系方式

- **Issues**: [GitHub Issues](https://github.com/{owner}/{repo}/issues)
- **Discussions**: [GitHub Discussions](https://github.com/{owner}/{repo}/discussions)

---

<div align="center">

**⭐️ 如果觉得有用,请给个 Star! ⭐️**

Made with 🤖 by AI • Curated with ❤️ by Human

[⬆️ 回到顶部](#ai-readwise)

</div>
