"""
Translation service using LangChain OpenAI.

Provides document translation with domain-aware terminology.
Supports progress logging and resume from interrupted translations.
Uses separate chunk files for efficient storage and resume.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Language codes
LANG_ZH = 'zh'
LANG_EN = 'en'
LANG_NAMES = {
    LANG_ZH: 'Chinese',
    LANG_EN: 'English',
}

# Chunk size - 80K chars for modern models (gpt-4o, qwen-turbo support 128K tokens)
# 80K chars ≈ 25K tokens, balances context preservation with API limits
DEFAULT_CHUNK_SIZE = 80000

# Max retries for LLM validation failures
MAX_RETRIES = 2


class TranslationService:
    """Service for translating documents using LLM."""
    
    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.models = [m.strip() for m in os.getenv("LLM_MODELS", "gpt-4o-mini").split(",") if m.strip()]
        self.default_model = os.getenv("LLM_DEFAULT_MODEL", self.models[0] if self.models else "gpt-4o-mini")
        self._cancelled: dict = {}
    
    def cancel_translation(self, book_id: str):
        """Request cancellation of translation for a book."""
        self._cancelled[book_id] = True
        logger.info(f"[Translation] Cancellation requested for: {book_id}")
    
    def is_cancelled(self, book_id: str) -> bool:
        """Check if translation for a book is cancelled."""
        return self._cancelled.get(book_id, False)
    
    def clear_cancellation(self, book_id: str):
        """Clear cancellation flag for a book."""
        if book_id in self._cancelled:
            del self._cancelled[book_id]
    
    def get_available_models(self) -> list[str]:
        """Get list of available LLM models."""
        return self.models
    
    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
    
    def _create_llm(self, model: str, streaming: bool = False):
        """Create a LangChain ChatOpenAI instance with optional streaming."""
        return ChatOpenAI(
            model=model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0.3,
            streaming=streaming,
        )
    
    def detect_language(self, content: str) -> str:
        """Detect language of content. Returns 'zh' or 'en'."""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', content))
        
        if total_chars == 0:
            return LANG_EN
        
        chinese_ratio = chinese_chars / total_chars
        return LANG_ZH if chinese_ratio > 0.3 else LANG_EN
    
    def detect_domain(self, content: str, model: str) -> str:
        """Detect document domain using LLM."""
        logger.info("[Translation] Detecting document domain...")
        llm = self._create_llm(model)
        
        sample = content[:3000]
        prompt = f"""Analyze the following text and identify its primary domain/field.
Reply with ONLY the domain name in English (e.g., "computer science", "medicine", "business").
Do not include any other text.

Text sample:
{sample}

Domain:"""
        
        try:
            response = llm.invoke(prompt)
            domain = response.content.strip().lower().strip('"\'')
            logger.info(f"[Translation] Detected domain: {domain}")
            return domain
        except Exception as e:
            logger.error(f"[Translation] Failed to detect domain: {e}")
            return "general"
    
    def _chunk_content(self, content: str, max_chars: int = DEFAULT_CHUNK_SIZE) -> list[str]:
        """
        Split content into chunks, preserving markdown structure.
        Uses 80K chars default for fewer, larger chunks.
        """
        if len(content) <= max_chars:
            return [content]
        
        # Try to split by chapter headers first (# or ##)
        chapter_pattern = r'\n(?=# )'
        chapters = re.split(chapter_pattern, content)
        
        if len(chapters) > 1:
            # Merge small chapters, split large ones
            return self._merge_and_split_sections(chapters, max_chars)
        
        # Fallback: split by paragraphs
        paragraphs = content.split('\n\n')
        return self._merge_paragraphs(paragraphs, max_chars)
    
    def _merge_and_split_sections(self, sections: list[str], max_chars: int) -> list[str]:
        """Merge small sections and split large ones."""
        chunks = []
        current = ""
        
        for section in sections:
            if len(section) > max_chars:
                # Save current chunk
                if current:
                    chunks.append(current.strip())
                    current = ""
                # Split large section by paragraphs
                paragraphs = section.split('\n\n')
                sub_chunks = self._merge_paragraphs(paragraphs, max_chars)
                chunks.extend(sub_chunks)
            elif len(current) + len(section) + 1 > max_chars:
                if current:
                    chunks.append(current.strip())
                current = section
            else:
                current = current + "\n" + section if current else section
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    def _merge_paragraphs(self, paragraphs: list[str], max_chars: int) -> list[str]:
        """Merge paragraphs into chunks up to max_chars."""
        chunks = []
        current = ""
        
        for para in paragraphs:
            if len(para) > max_chars:
                if current:
                    chunks.append(current.strip())
                    current = ""
                chunks.append(para.strip())
            elif len(current) + len(para) + 2 > max_chars:
                if current:
                    chunks.append(current.strip())
                current = para
            else:
                current = current + "\n\n" + para if current else para
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    
    def _get_progress_file(self, target_dir: Path, target_lang: str) -> Path:
        """Get path to translation progress file."""
        return target_dir / f"translation_progress_{target_lang}.json"
    
    def _get_chunk_file(self, target_dir: Path, index: int) -> Path:
        """Get path to individual chunk file."""
        return target_dir / f"_chunk_{index:03d}.txt"
    
    def _save_progress(self, progress_file: Path, data: dict):
        """Save progress metadata to file (lightweight, no content)."""
        progress_file.parent.mkdir(parents=True, exist_ok=True)
        progress_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def _load_progress(self, progress_file: Path) -> Optional[dict]:
        """Load progress metadata from file."""
        if not progress_file.exists():
            return None
        try:
            return json.loads(progress_file.read_text(encoding='utf-8'))
        except Exception as e:
            logger.warning(f"[Translation] Failed to load progress: {e}")
            return None
    
    def _save_chunk(self, target_dir: Path, index: int, content: str):
        """Save translated chunk to individual file."""
        chunk_file = self._get_chunk_file(target_dir, index)
        chunk_file.write_text(content, encoding='utf-8')
    
    def _load_chunk(self, target_dir: Path, index: int) -> Optional[str]:
        """Load translated chunk from file."""
        chunk_file = self._get_chunk_file(target_dir, index)
        if chunk_file.exists():
            return chunk_file.read_text(encoding='utf-8')
        return None
    
    def _cleanup_chunks(self, target_dir: Path, total_chunks: int):
        """Remove individual chunk files after merge."""
        for i in range(total_chunks):
            chunk_file = self._get_chunk_file(target_dir, i)
            if chunk_file.exists():
                chunk_file.unlink()
    
    def _validate_translation(self, output: str, source_lang: str, target_lang: str) -> bool:
        """
        Validate translation output.
        Returns False if output appears to be system prompt or wrong language.
        """
        # Check for system prompt keywords
        invalid_patterns = [
            "Important rules",
            "IMPORTANT RULES",
            "Preserve ALL markdown",
            "Keep ALL markdown formatting",
            "Keep all image references",
            "Keep image references",
        ]
        
        for pattern in invalid_patterns:
            if pattern in output:
                logger.warning(f"[Translation] Validation failed: found '{pattern}' in output")
                return False
        
        # Check output language matches target
        detected_lang = self.detect_language(output)
        if detected_lang != target_lang:
            # Allow if content is mostly code/tables (may have mixed languages)
            code_ratio = len(re.findall(r'```|`[^`]+`|\|.*\|', output)) / max(len(output), 1)
            if code_ratio < 0.1:
                logger.warning(f"[Translation] Validation failed: expected {target_lang}, got {detected_lang}")
                return False
        
        return True

    def get_progress(self, target_dir: Path, target_lang: str) -> int:
        """Get current translation progress percentage."""
        progress_file = self._get_progress_file(target_dir, target_lang)
        data = self._load_progress(progress_file)
        
        if not data:
            return 0
        
        completed = len(data.get('completed_chunks', []))
        total = data.get('total_chunks', 0)
        
        if total == 0:
            return 0
        
        return int((completed / total) * 100)
    
    def translate_content(
        self,
        content: str,
        source_lang: str,
        target_lang: str,
        model: str,
        domain: str,
        target_dir: Path,
        book_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Translate content with separate chunk file storage.
        Supports resume from interrupted translation.
        """
        self.clear_cancellation(book_id)
        
        if source_lang == target_lang:
            return content
        
        llm = self._create_llm(model, streaming=True)
        source_name = LANG_NAMES.get(source_lang, source_lang)
        target_name = LANG_NAMES.get(target_lang, target_lang)
        
        # Chunk content
        chunks = self._chunk_content(content)
        total_chunks = len(chunks)
        
        logger.info(f"[Translation] Translating {total_chunks} chunks from {source_lang} to {target_lang}")
        
        # Load existing progress
        progress_file = self._get_progress_file(target_dir, target_lang)
        progress_data = self._load_progress(progress_file)
        
        completed_chunks = set()
        effective_domain = domain
        
        # Resume from saved progress
        if progress_data and progress_data.get('total_chunks') == total_chunks:
            completed_chunks = set(progress_data.get('completed_chunks', []))
            if progress_data.get('domain'):
                effective_domain = progress_data['domain']
                logger.info(f"[Translation] Resuming with saved domain: {effective_domain}")
            if completed_chunks:
                logger.info(f"[Translation] Resuming: {len(completed_chunks)}/{total_chunks} chunks done")
        
        # Translate each chunk
        for i in range(total_chunks):
            # Skip completed chunks
            if i in completed_chunks:
                continue
            
            # Check cancellation
            if self.is_cancelled(book_id):
                logger.info(f"[Translation] Cancelled at chunk {i+1}/{total_chunks}")
                raise InterruptedError(f"Translation cancelled for {book_id}")
            
            chunk = chunks[i]
            pct = int(((i + 1) / total_chunks) * 100)
            msg = f"Translating... ({i+1}/{total_chunks})"
            
            logger.info(f"[Translation] Progress: {pct}% - {msg}")
            if progress_callback:
                progress_callback(int((i / total_chunks) * 100), msg)
            
            # Enhanced prompt with clear role and explicit language specification
            system_prompt = f"""# Role
You are a senior expert and professional translator in the field of **{effective_domain}**.
You have deep knowledge of {effective_domain} terminology and concepts.

# Task
Translate the following text from **{source_name}** to **{target_name}**.

# Critical Requirements
1. **Output Language**: Your translation MUST be in {target_name}. Do not output {source_name}.
2. **Domain Expertise**: Use accurate and professional {effective_domain} terminology.
3. **Markdown Preservation**: Keep ALL markdown formatting exactly as-is:
   - Headers (# ## ###)
   - Lists (- * 1.)
   - Code blocks (```)
   - Links ([text](url))
   - Images (![](path)) - DO NOT modify image paths
4. **No Additions**: Output ONLY the translated text. No explanations, notes, or comments.
5. **Structure**: Maintain the original paragraph and section structure.

# Language Reminder
Source: {source_name} → Target: {target_name}
Your output must be entirely in {target_name}."""
            
            user_prompt = f"""Please translate the following {source_name} text to {target_name}:

{chunk}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Try translation with retries using streaming
            translated = None
            for attempt in range(MAX_RETRIES + 1):
                try:
                    # Use streaming for better handling of long responses
                    output_chunks = []
                    for chunk_response in llm.stream(messages):
                        # Check for cancellation during streaming
                        if self.is_cancelled(book_id):
                            logger.info(f"[Translation] Cancelled during streaming at chunk {i+1}/{total_chunks}")
                            # Save progress before raising
                            self._save_progress(progress_file, {
                                'total_chunks': total_chunks,
                                'completed_chunks': sorted(completed_chunks),
                                'domain': effective_domain,
                                'model': model,
                                'source_lang': source_lang,
                                'target_lang': target_lang
                            })
                            raise InterruptedError(f"Translation cancelled for {book_id}")
                        if chunk_response.content:
                            output_chunks.append(chunk_response.content)
                    output = "".join(output_chunks)
                    
                    # Validate output
                    if self._validate_translation(output, source_lang, target_lang):
                        translated = output
                        break
                    else:
                        logger.warning(f"[Translation] Chunk {i+1} validation failed, attempt {attempt+1}")
                        if attempt == MAX_RETRIES:
                            # Use output anyway but log warning
                            logger.error(f"[Translation] Using invalid output for chunk {i+1} after {MAX_RETRIES} retries")
                            translated = output
                except InterruptedError:
                    # Re-raise cancellation
                    raise
                except Exception as e:
                    logger.error(f"[Translation] Chunk {i+1} failed: {e}")
                    if attempt == MAX_RETRIES:
                        raise
            
            # Save chunk to separate file
            self._save_chunk(target_dir, i, translated)
            completed_chunks.add(i)
            
            # Update progress (lightweight, only indices)
            self._save_progress(progress_file, {
                'total_chunks': total_chunks,
                'completed_chunks': sorted(completed_chunks),
                'domain': effective_domain,
                'model': model,
                'source_lang': source_lang,
                'target_lang': target_lang
            })
        
        logger.info(f"[Translation] All {total_chunks} chunks completed, merging...")
        
        # Merge all chunks
        translated_parts = []
        for i in range(total_chunks):
            chunk_content = self._load_chunk(target_dir, i)
            if chunk_content:
                translated_parts.append(chunk_content)
        
        final_content = "\n\n".join(translated_parts)
        
        # Cleanup
        self._cleanup_chunks(target_dir, total_chunks)
        if progress_file.exists():
            progress_file.unlink()
        
        if progress_callback:
            progress_callback(100, "Translation completed")
        
        return final_content
    
    def translate_document(
        self,
        source_md_path: Path,
        target_dir: Path,
        target_lang: str,
        model: str,
        book_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Path:
        """Translate a source markdown document to target language."""
        logger.info(f"[Translation] Starting: {source_md_path} -> {target_lang}")
        
        content = source_md_path.read_text(encoding='utf-8')
        source_lang = self.detect_language(content)
        logger.info(f"[Translation] Source language: {source_lang}")
        
        if source_lang == target_lang:
            logger.info("[Translation] Same language, skipping")
            return source_md_path
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for saved domain
        progress_file = self._get_progress_file(target_dir, target_lang)
        progress_data = self._load_progress(progress_file)
        
        if progress_data and progress_data.get('domain'):
            domain = progress_data['domain']
            logger.info(f"[Translation] Using saved domain: {domain}")
            if progress_callback:
                progress_callback(2, f"Using saved domain: {domain}")
        else:
            if progress_callback:
                progress_callback(1, "Detecting document domain...")
            domain = self.detect_domain(content, model)
        
        if progress_callback:
            progress_callback(3, "Starting translation...")
        
        translated_content = self.translate_content(
            content=content,
            source_lang=source_lang,
            target_lang=target_lang,
            model=model,
            domain=domain,
            target_dir=target_dir,
            book_id=book_id,
            progress_callback=lambda pct, msg: progress_callback(3 + int(pct * 0.97), msg) if progress_callback else None
        )
        
        target_filename = f"{source_md_path.stem}_{target_lang}.md"
        target_path = target_dir / target_filename
        target_path.write_text(translated_content, encoding='utf-8')
        
        logger.info(f"[Translation] Saved: {target_path}")
        
        if progress_callback:
            progress_callback(100, "Translation completed")
        
        return target_path


# Singleton instance
translation_service = TranslationService()
