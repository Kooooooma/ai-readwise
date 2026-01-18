"""
Summary Service - Generate chapter summaries using LLM.

Extracts key points, conclusions, examples, and generates voice scripts
for podcast preparation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating chapter summaries using LLM."""
    
    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.models = [m.strip() for m in os.getenv("LLM_MODELS", "gpt-4o-mini").split(",") if m.strip()]
        self.default_model = os.getenv("LLM_DEFAULT_MODEL", self.models[0] if self.models else "gpt-4o-mini")
    
    def _create_llm(self, model: str):
        """Create a LangChain ChatOpenAI instance."""
        return ChatOpenAI(
            model=model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=0.5,  # Slightly higher for creative summarization
        )
    
    def _get_summary_file(self, chapter_dir: Path, chapter_filename: str) -> Path:
        """Get path to summary JSON file. Stored in summaries/ subfolder."""
        # Remove .md extension and add _summary.json
        stem = Path(chapter_filename).stem
        summaries_dir = chapter_dir / "summaries"
        return summaries_dir / f"{stem}_summary.json"
    
    def get_summary(self, chapter_dir: Path, chapter_filename: str) -> Optional[Dict[str, Any]]:
        """Load existing summary from file. Returns None if invalid or incomplete."""
        summary_file = self._get_summary_file(chapter_dir, chapter_filename)
        if not summary_file.exists():
            return None
        try:
            data = json.loads(summary_file.read_text(encoding='utf-8'))
            # Validate summary has required content
            if not data.get('voice_script'):
                logger.warning(f"[Summary] Invalid summary (no voice_script): {summary_file}")
                return None
            return data
        except Exception as e:
            logger.error(f"[Summary] Failed to load summary: {e}")
            return None
    
    def save_summary(self, chapter_dir: Path, chapter_filename: str, data: Dict[str, Any]) -> bool:
        """Save summary to file."""
        summary_file = self._get_summary_file(chapter_dir, chapter_filename)
        try:
            summary_file.parent.mkdir(parents=True, exist_ok=True)
            summary_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            logger.info(f"[Summary] Saved: {summary_file}")
            return True
        except Exception as e:
            logger.error(f"[Summary] Failed to save: {e}")
            return False
    
    def _get_mp3_file(self, chapter_dir: Path, chapter_filename: str) -> Path:
        """Get path to MP3 file. Same location as summary JSON."""
        stem = Path(chapter_filename).stem
        summaries_dir = chapter_dir / "summaries"
        return summaries_dir / f"{stem}_voice.mp3"
    
    def get_mp3_path(self, chapter_dir: Path, chapter_filename: str) -> Optional[Path]:
        """Get MP3 path if it exists and has valid content (>1KB)."""
        mp3_file = self._get_mp3_file(chapter_dir, chapter_filename)
        if mp3_file.exists():
            try:
                file_size = mp3_file.stat().st_size
                # Only consider valid if > 1KB (empty/partial files are invalid)
                if file_size > 1024:
                    return mp3_file
                else:
                    # Try to delete invalid empty file
                    logger.warning(f"[Summary] Removing invalid MP3 (too small): {mp3_file}")
                    try:
                        mp3_file.unlink()
                    except PermissionError:
                        logger.warning(f"[Summary] Cannot delete MP3 (in use): {mp3_file}")
                        return None  # Don't regenerate if file is in use
            except Exception as e:
                logger.error(f"[Summary] Error checking MP3: {e}")
        return None
    
    def delete_mp3(self, chapter_dir: Path, chapter_filename: str) -> bool:
        """Delete MP3 file if exists."""
        mp3_file = self._get_mp3_file(chapter_dir, chapter_filename)
        if mp3_file.exists():
            try:
                mp3_file.unlink()
                logger.info(f"[Summary] Deleted MP3: {mp3_file}")
                return True
            except Exception as e:
                logger.error(f"[Summary] Failed to delete MP3: {e}")
        return False
    
    async def generate_mp3(
        self, 
        chapter_dir: Path, 
        chapter_filename: str, 
        voice_script: str,
        lang: str = 'zh'
    ) -> Optional[Path]:
        """Generate MP3 from voice script using edge-tts."""
        import edge_tts
        
        mp3_file = self._get_mp3_file(chapter_dir, chapter_filename)
        
        # Select voice based on language
        voices = {
            'zh': 'zh-CN-YunjianNeural',  # Chinese male voice
            'en': 'en-US-GuyNeural',       # English male voice
        }
        voice = voices.get(lang, 'zh-CN-YunjianNeural')
        
        try:
            mp3_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"[Summary] Generating MP3 with voice {voice}...")
            communicate = edge_tts.Communicate(voice_script, voice)
            await communicate.save(str(mp3_file))
            
            file_size = mp3_file.stat().st_size
            logger.info(f"[Summary] MP3 generated: {mp3_file} ({file_size / 1024:.1f} KB)")
            return mp3_file
            
        except Exception as e:
            logger.error(f"[Summary] Failed to generate MP3: {e}")
            return None
    
    def generate_summary(
        self,
        chapter_content: str,
        chapter_title: str,
        domain: str,
        target_lang: str = 'en',
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate summary for a chapter using LLM.
        
        Args:
            chapter_content: Full markdown content of the chapter
            chapter_title: Title of the chapter
            domain: Domain/field of the book (e.g., "software engineering")
            model: LLM model to use
            
        Returns:
            Summary dict with key_points, conclusions, examples, voice_script
        """
        model = model or self.default_model
        llm = self._create_llm(model)
        
        # Map language code to display name
        lang_names = {'zh': 'Chinese (中文)', 'en': 'English'}
        lang_name = lang_names.get(target_lang, 'English')
        
        logger.info(f"[Summary] Generating summary for: {chapter_title} in {lang_name}")
        
        system_prompt = f"""# Role
You are a senior expert in **{domain}** and a skilled content curator.
Your task is to extract and distill knowledge from book chapters.

# Output Format
You must respond with a valid JSON object (no markdown code blocks) containing:

{{
  "key_points": ["point 1", "point 2", ...],
  "conclusions": ["conclusion 1", ...],
  "examples": ["example 1", ...],
  "voice_script": "A spoken summary..."
}}

# Requirements

## key_points (3-5 items)
- Core concepts and ideas presented in this chapter
- Each point should be 1-2 sentences

## conclusions (2-3 items)
- Main takeaways and insights a reader should remember
- Actionable or memorable statements

## examples (2-3 items)
- Real-world examples, case studies, or analogies used
- Brief description of each example and what it illustrates

## voice_script (CRITICAL)
- A narrative script for audio podcast narration
- Must be **300-400 words** (approximately 2 minutes when spoken)
- Should flow naturally as spoken content
- Cover ALL key knowledge from the chapter
- Use conversational but professional tone
- Start with "In this chapter..." or similar intro
- Use {domain} terminology accurately

# Language (CRITICAL)
- Output language: **{lang_name}**
- ALL content (key_points, conclusions, examples, voice_script) MUST be in {lang_name}
- Do NOT output in any other language"""

        def build_user_prompt(content_text: str) -> str:
            return f"""Please generate a comprehensive summary for this chapter.

Chapter Title: {chapter_title}

Chapter Content:
{content_text}"""

        def try_generate(content_text: str):
            """Try to generate summary with given content."""
            user_prompt = build_user_prompt(content_text)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            return llm.invoke(messages)
        
        # Try with full content first, truncate on token error
        content_to_use = chapter_content
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[Summary] Attempt {attempt + 1}: sending {len(content_to_use)} chars")
                response = try_generate(content_to_use)
                content = response.content.strip()
                
                # Try to parse JSON from response
                # Handle possible markdown code blocks
                if content.startswith("```"):
                    # Extract JSON from code block
                    lines = content.split("\n")
                    json_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```") and not in_block:
                            in_block = True
                            continue
                        elif line.startswith("```") and in_block:
                            break
                        elif in_block:
                            json_lines.append(line)
                    content = "\n".join(json_lines)
                
                summary_data = json.loads(content)
                
                # Add metadata
                summary_data["generated_at"] = datetime.now().isoformat()
                summary_data["domain"] = domain
                summary_data["model"] = model
                summary_data["chapter_title"] = chapter_title
                
                logger.info(f"[Summary] Generated successfully for: {chapter_title}")
                return summary_data
                
            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a token limit error
                if any(kw in error_str for kw in ['token', 'length', 'too long', 'context', 'maximum']):
                    if attempt < max_retries - 1:
                        # Truncate to 60k chars and retry
                        truncate_size = 60000
                        logger.warning(f"[Summary] Token limit hit, truncating to {truncate_size} chars and retrying...")
                        content_to_use = chapter_content[:truncate_size]
                        continue
                
                # Check if it's a JSON parse error
                if isinstance(e, json.JSONDecodeError):
                    logger.error(f"[Summary] Failed to parse LLM response as JSON: {e}")
                    logger.error(f"[Summary] Response was: {response.content[:500]}...")
                    return {
                        "generated_at": datetime.now().isoformat(),
                        "domain": domain,
                        "model": model,
                        "chapter_title": chapter_title,
                        "key_points": ["Failed to generate - please try again"],
                        "conclusions": [],
                        "examples": [],
                        "voice_script": "",
                        "error": f"JSON parse error: {str(e)}"
                    }
                
                logger.error(f"[Summary] Generation failed: {e}")
                raise


# Singleton instance
summary_service = SummaryService()
