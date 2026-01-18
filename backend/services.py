"""
Business logic services for the AI-Readwise API.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Callable
from .models import Book, Chapter, ExtractProgress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing scripts
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from split_markdown import split_markdown_file


class BookService:
    """Service for managing books."""
    
    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir
    
    def parse_description(self, content: str) -> Dict[str, str]:
        """Parse description.md content (YAML-like format)."""
        result = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result
    
    def get_all_books(self) -> List[Book]:
        """Get all books from resources directory."""
        books = []
        
        if not self.resources_dir.exists():
            return books
        
        for book_dir in self.resources_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            description_file = book_dir / "description.md"
            if not description_file.exists():
                continue
            
            try:
                content = description_file.read_text(encoding='utf-8')
                data = self.parse_description(content)
                
                # Check if chapters directory exists AND has actual chapter files
                pdf_file = data.get('file', '')
                chapter_dir_name = Path(pdf_file).stem if pdf_file else ''
                chapter_dir = book_dir / chapter_dir_name
                
                # Count actual .md chapter files (exclude progress file and source file)
                has_chapters = False
                if chapter_dir.exists() and chapter_dir.is_dir():
                    chapter_files = [f for f in chapter_dir.glob('*.md') 
                                    if not f.name.startswith('.')]
                    has_chapters = len(chapter_files) > 1  # More than just the source md
                
                book = Book(
                    id=book_dir.name,
                    title=data.get('title', book_dir.name),
                    description=data.get('description', ''),
                    file=pdf_file,
                    has_chapters=has_chapters
                )
                books.append(book)
            except Exception as e:
                logger.error(f"Error loading book {book_dir.name}: {e}")
                continue
        
        return books
    
    def get_book(self, book_id: str) -> Optional[Book]:
        """Get a specific book by ID."""
        books = self.get_all_books()
        for book in books:
            if book.id == book_id:
                return book
        return None
    
    def get_chapters(self, book_id: str) -> List[Chapter]:
        """Get all chapters of a book."""
        book = self.get_book(book_id)
        if not book or not book.has_chapters:
            return []
        
        book_dir = self.resources_dir / book_id
        chapter_dir_name = Path(book.file).stem
        chapter_dir = book_dir / chapter_dir_name
        
        if not chapter_dir.exists():
            return []
        
        chapters = []
        # Only include numbered chapter files (e.g., 01_xxx.md, 02_xxx.md)
        # This excludes the source markdown file which doesn't have numbered prefix
        md_files = sorted([
            f for f in chapter_dir.iterdir() 
            if f.suffix.lower() == '.md' 
            and len(f.stem) > 2 
            and f.stem[:2].isdigit() 
            and f.stem[2] == '_'
        ])
        
        for idx, md_file in enumerate(md_files):
            # Extract display name from filename
            name = md_file.stem
            # Remove numbering prefix if exists (e.g., "01_" -> "")
            if len(name) > 3 and name[2] == '_':
                display_name = name[3:]
            else:
                display_name = name
            
            chapters.append(Chapter(
                name=display_name,
                filename=md_file.name,
                order=idx
            ))
        
        return chapters
    
    def get_chapter_content(self, book_id: str, chapter_filename: str) -> Optional[str]:
        """Get the content of a specific chapter."""
        book = self.get_book(book_id)
        if not book:
            return None
        
        book_dir = self.resources_dir / book_id
        chapter_dir_name = Path(book.file).stem
        chapter_file = book_dir / chapter_dir_name / chapter_filename
        
        if not chapter_file.exists():
            return None
        
        return chapter_file.read_text(encoding='utf-8')
    
    def get_source_markdown(self, book_id: str) -> Optional[str]:
        """
        Get the source (original) markdown file content.
        This is the full document before chapter splitting.
        """
        book = self.get_book(book_id)
        if not book:
            return None
        
        book_dir = self.resources_dir / book_id
        output_dir = book_dir / Path(book.file).stem
        source_md_name = Path(book.file).stem + ".md"
        source_md_path = output_dir / source_md_name
        
        # If path is too long, it may have been shortened with a hash
        if not source_md_path.exists():
            from backend.marker_extract import _shorten_path
            shortened_path = _shorten_path(source_md_path)
            if shortened_path != source_md_path and shortened_path.exists():
                source_md_path = shortened_path
        
        # Fallback: check if source md is in book_dir directly
        if not source_md_path.exists():
            source_md_path = book_dir / source_md_name
        
        if not source_md_path.exists():
            logger.warning(f"Source markdown not found: {source_md_path}")
            return None
        
        logger.info(f"[BookService] Reading source markdown: {source_md_path}")
        return source_md_path.read_text(encoding='utf-8')
    
    def update_source_markdown(self, book_id: str, content: str) -> bool:
        """
        Update the source markdown file content.
        Used for editing/proofreading before re-splitting.
        """
        book = self.get_book(book_id)
        if not book:
            return False
        
        book_dir = self.resources_dir / book_id
        source_md_name = Path(book.file).stem + ".md"
        source_md_path = book_dir / Path(book.file).stem / source_md_name
        
        # Fallback: check if source md is in book_dir directly
        if not source_md_path.exists():
            source_md_path = book_dir / source_md_name
        
        if not source_md_path.exists():
            logger.warning(f"Source markdown not found for update: {source_md_path}")
            return False
        
        logger.info(f"[BookService] Updating source markdown: {source_md_path}")
        source_md_path.write_text(content, encoding='utf-8')
        return True
    
    def resplit_chapters(self, book_id: str) -> int:
        """
        Re-split the source markdown into chapters.
        Deletes existing chapter files and regenerates them.
        
        Returns:
            Number of chapters created
        """
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Book not found: {book_id}")
        
        book_dir = self.resources_dir / book_id
        chapter_dir = book_dir / Path(book.file).stem
        source_md_name = Path(book.file).stem + ".md"
        source_md_path = chapter_dir / source_md_name
        
        # If path is too long, it may have been shortened with a hash
        if not source_md_path.exists():
            from backend.marker_extract import _shorten_path
            shortened_path = _shorten_path(source_md_path)
            if shortened_path != source_md_path and shortened_path.exists():
                source_md_path = shortened_path
                source_md_name = source_md_path.name
        
        # Fallback: check if source md is in book_dir directly
        if not source_md_path.exists():
            source_md_path = book_dir / source_md_name
        
        if not source_md_path.exists():
            raise FileNotFoundError(f"Source markdown not found: {source_md_path}")
        
        logger.info(f"[BookService] Re-splitting chapters for: {book_id}")
        
        # Step 1: Delete existing chapter files (keep source md and images)
        if chapter_dir.exists():
            for f in chapter_dir.iterdir():
                # Keep the source markdown, progress file, and images folder
                if f.name == source_md_name or f.name == "images" or f.name.startswith('.'):
                    continue
                if f.suffix.lower() == '.md':
                    logger.info(f"[BookService] Deleting chapter: {f.name}")
                    f.unlink()
        
        # Step 2: Fix image paths before splitting
        from backend.fix_markdown_images import fix_image_paths
        fix_count = fix_image_paths(source_md_path)
        logger.info(f"[BookService] Fixed {fix_count} image paths")
        
        # Step 3: Re-split using split_markdown
        logger.info(f"[BookService] Splitting: {source_md_path} -> {chapter_dir}")
        split_markdown_file(source_md_path, chapter_dir)
        
        # Count created chapters (excluding source md)
        chapter_files = [
            f for f in chapter_dir.glob('*.md') 
            if f.name != source_md_name
        ]
        
        logger.info(f"[BookService] Created {len(chapter_files)} chapters")
        return len(chapter_files)
    
    def get_language_info(self, book_id: str) -> dict:
        """
        Get language information for a book.
        Returns source language and available translations.
        """
        from .translation_service import translation_service, LANG_ZH, LANG_EN
        
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Book not found: {book_id}")
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        source_dir = book_dir / pdf_stem
        
        # Get source markdown to detect language
        source_md = self._find_source_md(book_id)
        source_lang = LANG_EN  # Default
        
        if source_md and source_md.exists():
            sample = source_md.read_text(encoding='utf-8')[:2000]
            source_lang = translation_service.detect_language(sample)
            
            # Use the actual source dir name as the stem (handles shortened paths)
            pdf_stem = source_md.parent.name
        else:
             # Fallback if source_md not found (should be rare)
             pdf_stem = Path(book.file).stem

        
        # Check for available translations and progress
        available_langs = [source_lang]
        translation_progress = {}
        
        for lang in [LANG_ZH, LANG_EN]:
            if lang != source_lang:
                lang_dir = book_dir / f"{pdf_stem}_{lang}"
                
                # Check for completed translation
                if lang_dir.exists() and any(lang_dir.glob('*.md')):
                    available_langs.append(lang)
                
                # Check for partial progress
                progress = translation_service.get_progress(lang_dir, lang)
                if progress > 0:
                    translation_progress[lang] = progress
        
        return {
            "source_lang": source_lang,
            "available_langs": available_langs,
            "has_translation": {
                LANG_ZH: LANG_ZH in available_langs,
                LANG_EN: LANG_EN in available_langs
            },
            "translation_progress": translation_progress
        }
    
    def _find_source_md(self, book_id: str) -> Optional[Path]:
        """Find source markdown file for a book."""
        book = self.get_book(book_id)
        if not book:
            return None
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        source_dir = book_dir / pdf_stem
        source_md_name = pdf_stem + ".md"
        source_md_path = source_dir / source_md_name
        
        # Try shortened path
        if not source_md_path.exists():
            from backend.marker_extract import _shorten_path
            shortened_path = _shorten_path(source_md_path)
            if shortened_path != source_md_path and shortened_path.exists():
                return shortened_path
        
        return source_md_path if source_md_path.exists() else None
    
    def get_chapter_dir(self, book_id: str, lang: str) -> Optional[Path]:
        """Get the chapter directory path for a specific language."""
        book = self.get_book(book_id)
        if not book:
            return None
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        
        # Get the correct stem from _find_source_md logic
        source_md = self._find_source_md(book_id)
        if source_md:
            pdf_stem = source_md.parent.name
        
        lang_info = self.get_language_info(book_id)
        source_lang = lang_info["source_lang"]
        
        if lang == source_lang:
            chapter_dir = book_dir / pdf_stem
        else:
            chapter_dir = book_dir / f"{pdf_stem}_{lang}"
        
        return chapter_dir if chapter_dir.exists() else None
    
    def get_chapters_for_lang(self, book_id: str, lang: str) -> List[Chapter]:
        """Get chapters for a specific language version."""
        from .translation_service import LANG_ZH, LANG_EN
        
        book = self.get_book(book_id)
        if not book:
            return []
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        
        # Detect source language and valid stem
        lang_info = self.get_language_info(book_id)
        source_lang = lang_info["source_lang"]
        
        # Get the correct stem from _find_source_md logic (via source_dir)
        source_md = self._find_source_md(book_id)
        if source_md:
            pdf_stem = source_md.parent.name
        
        # Determine which directory to use
        if lang == source_lang:
            chapter_dir = book_dir / pdf_stem
        else:
            chapter_dir = book_dir / f"{pdf_stem}_{lang}"
        
        if not chapter_dir.exists():
            return []
        
        # Find all chapter files (numbered prefix like 01_, 02_)
        chapter_files = sorted([
            f for f in chapter_dir.glob('[0-9][0-9]_*.md')
        ])
        
        return [
            Chapter(
                name=f.stem.split('_', 1)[1] if '_' in f.stem else f.stem,
                filename=f.name,
                order=int(f.stem[:2]) if f.stem[:2].isdigit() else 0
            )
            for f in chapter_files
        ]
    
    def get_chapter_content_for_lang(self, book_id: str, lang: str, chapter_filename: str) -> Optional[str]:
        """Get chapter content for a specific language."""
        from .translation_service import LANG_ZH, LANG_EN
        
        book = self.get_book(book_id)
        if not book:
            return None
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        
        lang_info = self.get_language_info(book_id)
        source_lang = lang_info["source_lang"]
        
        # Get the correct stem from _find_source_md logic
        source_md = self._find_source_md(book_id)
        if source_md:
            pdf_stem = source_md.parent.name
        
        if lang == source_lang:
            chapter_dir = book_dir / pdf_stem
        else:
            chapter_dir = book_dir / f"{pdf_stem}_{lang}"
        
        chapter_file = chapter_dir / chapter_filename
        if not chapter_file.exists():
            return None
        
        return chapter_file.read_text(encoding='utf-8')
    
    def translate_book(
        self, 
        book_id: str, 
        target_lang: str, 
        model: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> int:
        """
        Translate a book to target language.
        
        Returns number of chapters created.
        """
        from .translation_service import translation_service
        from split_markdown import split_markdown_file
        from .fix_markdown_images import fix_image_paths
        
        book = self.get_book(book_id)
        if not book:
            raise ValueError(f"Book not found: {book_id}")
        
        book_dir = self.resources_dir / book_id
        pdf_stem = Path(book.file).stem
        # Find source markdown
        source_md = self._find_source_md(book_id)
        if not source_md or not source_md.exists():
            raise FileNotFoundError(f"Source markdown not found for: {book_id}")
            
        # Use actual source directory name as stem (handles shortened paths)
        pdf_stem = source_md.parent.name
        source_dir = book_dir / pdf_stem
        target_dir = book_dir / f"{pdf_stem}_{target_lang}"
        
        logger.info(f"[BookService] Translating {book_id} to {target_lang}")
        
        # Translate the document
        translated_md = translation_service.translate_document(
            source_md_path=source_md,
            target_dir=target_dir,
            target_lang=target_lang,
            model=model,
            book_id=book_id,
            progress_callback=progress_callback
        )
        
        if progress_callback:
            progress_callback(85, "Fixing image paths...")
        
        # Fix image paths
        fix_image_paths(translated_md)
        
        # Copy images folder if not exists
        source_images = source_dir / "images"
        target_images = target_dir / "images"
        if source_images.exists() and not target_images.exists():
            import shutil
            shutil.copytree(source_images, target_images)
        
        if progress_callback:
            progress_callback(90, "Splitting chapters...")
        
        # Split into chapters
        split_markdown_file(translated_md, target_dir)
        
        # Count chapters
        chapter_count = len([f for f in target_dir.glob('[0-9][0-9]_*.md')])
        
        if progress_callback:
            progress_callback(100, f"Translation completed. Generated {chapter_count} chapters.")
        
        logger.info(f"[BookService] Translation completed, {chapter_count} chapters created")
        return chapter_count


class ExtractService:
    """
    Service for extracting PDF to markdown chapters.
    
    Uses multiprocessing for extraction to allow cancellation.
    Progress is persisted to files for recovery after page navigation.
    """
    
    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir
        self._processes: Dict[str, int] = {}  # book_id -> pid
    
    def get_extraction_status(self, book_id: str) -> Optional[ExtractProgress]:
        """
        Get current extraction status from progress file.
        
        This reads from the persisted progress file, allowing
        status retrieval after page navigation.
        """
        from .marker_extract import read_progress
        
        book_dir = self.resources_dir / book_id
        description_file = book_dir / "description.md"
        
        if not description_file.exists():
            return None
        
        # Get PDF filename to find output dir
        content = description_file.read_text(encoding='utf-8')
        data = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        pdf_filename = data.get('file')
        if not pdf_filename:
            return None
        
        output_dir = book_dir / Path(pdf_filename).stem
        progress_data = read_progress(output_dir)
        
        if not progress_data:
            return None
        
        # Check if the process is still running
        pid = progress_data.get('pid')
        if pid and progress_data.get('status') == 'extracting':
            import psutil
            try:
                process = psutil.Process(pid)
                if not process.is_running():
                    # Process died unexpectedly
                    progress_data['status'] = 'error'
                    progress_data['message'] = 'Extraction process terminated abnormally'
            except psutil.NoSuchProcess:
                progress_data['status'] = 'error'
                progress_data['message'] = 'Extraction process no longer exists'
        
        return ExtractProgress(
            status=progress_data.get('status', 'idle'),
            progress=progress_data.get('progress', 0),
            message=progress_data.get('message', ''),
            current_step=progress_data.get('current_step')
        )
    
    def cancel_extraction(self, book_id: str) -> bool:
        """
        Cancel an ongoing extraction by killing the process.
        
        Returns True if cancellation was successful.
        """
        from .marker_extract import read_progress, write_progress
        
        book_dir = self.resources_dir / book_id
        description_file = book_dir / "description.md"
        
        if not description_file.exists():
            return False
        
        content = description_file.read_text(encoding='utf-8')
        data = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        pdf_filename = data.get('file')
        if not pdf_filename:
            return False
        
        output_dir = book_dir / Path(pdf_filename).stem
        progress_data = read_progress(output_dir)
        
        if not progress_data:
            return False
        
        pid = progress_data.get('pid')
        if not pid:
            return False
        
        import psutil
        import signal
        
        try:
            process = psutil.Process(pid)
            # Kill the process tree (including child processes)
            children = process.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            process.terminate()
            
            # Wait a bit then force kill if needed
            gone, alive = psutil.wait_procs([process] + children, timeout=3)
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Update progress file to show cancelled
            write_progress(output_dir, 'cancelled', 0, 'Extraction cancelled', 'Cancelled')
            logger.info(f"[ExtractService] Cancelled extraction for {book_id}, killed PID {pid}")
            
            return True
            
        except psutil.NoSuchProcess:
            write_progress(output_dir, 'error', 0, 'Process no longer exists')
            return False
        except Exception as e:
            logger.error(f"[ExtractService] Failed to cancel: {e}")
            return False
    
    def cleanup_on_shutdown(self) -> int:
        """
        Clean up all unfinished extraction tasks on server shutdown.
        
        Kills any running worker processes and removes their progress files.
        Returns the number of tasks cleaned up.
        """
        import psutil
        import shutil
        from .marker_extract import read_progress, PROGRESS_FILE
        
        cleaned = 0
        
        # Scan all book directories for progress files
        if not self.resources_dir.exists():
            return 0
        
        for book_dir in self.resources_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            # Check all subdirectories for progress files
            for subdir in book_dir.iterdir():
                if not subdir.is_dir():
                    continue
                
                progress_file = subdir / PROGRESS_FILE
                if not progress_file.exists():
                    continue
                
                progress_data = read_progress(subdir)
                if not progress_data:
                    # Remove empty/corrupt progress file
                    try:
                        progress_file.unlink()
                        logger.info(f"[Cleanup] Removed empty progress file: {progress_file}")
                    except Exception:
                        pass
                    continue
                
                status = progress_data.get('status', '')
                pid = progress_data.get('pid')
                
                # Clean up in-progress tasks only
                # Keep 'completed' and 'extracted' (PDF done, split pending) for resume
                # 'extracted' allows resuming from split step
                if status in ('extracting', 'splitting'):
                    logger.info(f"[Cleanup] Found in-progress task in {subdir.name}, status={status}")
                    
                    # Try to kill the process if it's still running
                    if pid:
                        try:
                            process = psutil.Process(pid)
                            if process.is_running():
                                logger.info(f"[Cleanup] Killing worker process PID {pid}")
                                process.terminate()
                                process.wait(timeout=3)
                        except psutil.NoSuchProcess:
                            pass
                        except Exception as e:
                            logger.warning(f"[Cleanup] Failed to kill process {pid}: {e}")
                    
                    # Remove progress file
                    try:
                        progress_file.unlink()
                        logger.info(f"[Cleanup] Removed progress file: {progress_file}")
                    except Exception as e:
                        logger.warning(f"[Cleanup] Failed to remove progress file: {e}")
                    
                    # Remove the incomplete output directory if it only has progress/temp files
                    try:
                        md_files = list(subdir.glob('*.md'))
                        if len(md_files) <= 1:  # Only source md or none
                            shutil.rmtree(subdir)
                            logger.info(f"[Cleanup] Removed incomplete output dir: {subdir}")
                    except Exception as e:
                        logger.warning(f"[Cleanup] Failed to remove output dir: {e}")
                    
                    cleaned += 1
        
        if cleaned > 0:
            logger.info(f"[Cleanup] Cleaned up {cleaned} unfinished extraction task(s)")
        
        return cleaned
    
    async def extract_pdf(
        self, 
        book_id: str, 
        progress_callback: Optional[Callable[[ExtractProgress], None]] = None
    ) -> bool:
        """
        Extract PDF to markdown chapters using a subprocess.
        
        Runs extraction in a separate process for true cancellation support.
        Progress is read from the progress file written by the worker.
        """
        import subprocess
        import sys
        from .marker_extract import read_progress, write_progress
        
        book_dir = self.resources_dir / book_id
        description_file = book_dir / "description.md"
        
        # --- Step 0: Validate input ---
        if not description_file.exists():
            self._send_progress(book_id, 'error', 0, 'Book not found', progress_callback)
            return False
        
        content = description_file.read_text(encoding='utf-8')
        data = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        
        pdf_filename = data.get('file')
        if not pdf_filename:
            self._send_progress(book_id, 'error', 0, 'No PDF file specified', progress_callback)
            return False
        
        pdf_path = book_dir / pdf_filename
        if not pdf_path.exists():
            self._send_progress(book_id, 'error', 0, f'PDF file not found: {pdf_filename}', progress_callback)
            return False
        
        output_dir = book_dir / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[ExtractService] Starting extraction subprocess for: {pdf_path}")
        
        # --- Check if we can resume from a previous extraction ---
        existing_progress = read_progress(output_dir)
        is_resume = existing_progress and existing_progress.get('status') == 'extracted'
        
        if is_resume:
            logger.info(f"[ExtractService] Found 'extracted' status, will resume from split")
        else:
            # Only write extracting status if not resuming
            self._send_progress(book_id, 'extracting', 5, 
                               'Starting extraction process...', progress_callback, 'Starting')
        
        # Get the worker script path
        worker_script = Path(__file__).parent / "extract_worker.py"
        
        # Get the Python executable from the venv
        python_exe = sys.executable
        
        try:
            # Start the worker process
            # Don't capture stdout/stderr so worker logs appear in console
            process = subprocess.Popen(
                [python_exe, str(worker_script), str(pdf_path), str(output_dir)],
                cwd=str(Path(__file__).parent.parent),  # Project root
            )
            
            logger.info(f"[ExtractService] Started worker process PID: {process.pid}")
            
            # Only write initial progress if not resuming
            if not is_resume:
                write_progress(output_dir, 'extracting', 5, 'Worker started...', 'Starting', process.pid)
            
            # Poll for progress updates
            last_progress = None
            poll_count = 0
            while process.poll() is None:
                await asyncio.sleep(1)  # Check every second
                poll_count += 1
                
                # Read progress from file
                progress_data = read_progress(output_dir)
                
                if progress_data:
                    if progress_data != last_progress:
                        last_progress = progress_data
                        logger.info(f"[ExtractService] Progress: {progress_data.get('progress', 0)}% - {progress_data.get('current_step', 'N/A')}")
                        
                        # Send progress update
                        self._send_progress(
                            book_id,
                            progress_data.get('status', 'extracting'),
                            progress_data.get('progress', 0),
                            progress_data.get('message', ''),
                            progress_callback,
                            progress_data.get('current_step')
                        )
                else:
                    # No progress yet - log periodically to show we're still alive
                    if poll_count % 10 == 0:  # Every 10 seconds
                        logger.info(f"[ExtractService] Waiting for worker (PID {process.pid})... no progress yet")
            
            # Process finished - check result
            return_code = process.returncode
            process.wait()  # Ensure process is fully terminated
            
            if return_code != 0:
                logger.error(f"[ExtractService] Worker failed with code {return_code}")
                
                # Read final progress for error details
                progress_data = read_progress(output_dir)
                error_msg = progress_data.get('message', 'Extraction failed') if progress_data else 'Extraction failed'
                self._send_progress(book_id, 'error', 0, error_msg, progress_callback)
                return False
            
            # Read final progress
            progress_data = read_progress(output_dir)
            if progress_data:
                self._send_progress(
                    book_id,
                    progress_data.get('status', 'completed'),
                    progress_data.get('progress', 100),
                    progress_data.get('message', 'Completed'),
                    progress_callback,
                    progress_data.get('current_step', 'Completed')
                )
            
            logger.info(f"[ExtractService] Extraction completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ExtractService] Failed to start worker: {e}")
            self._send_progress(book_id, 'error', 0, f'Failed to start extraction: {str(e)}', progress_callback)
            return False
    
    def _send_progress(
        self, 
        book_id: str, 
        status: str, 
        progress: int, 
        message: str,
        callback: Optional[Callable[[ExtractProgress], None]] = None,
        current_step: Optional[str] = None
    ):
        """Send progress to callback (for SSE streaming)."""
        prog = ExtractProgress(
            status=status,
            progress=progress,
            message=message,
            current_step=current_step
        )
        
        logger.debug(f"[ExtractService] Progress: {status} {progress}% - {message}")
        
        if callback:
            callback(prog)

