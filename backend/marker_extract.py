"""
PDF Extraction using marker-pdf.

This module provides OCR-based PDF extraction for scanned PDFs.
Uses marker-pdf library which includes deep learning models for:
- Text detection and recognition (OCR)
- Layout analysis
- Table extraction

Progress is persisted to a JSON file for recovery after page navigation.
"""

import logging
import asyncio
import tempfile
import shutil
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Callable, Tuple, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Progress file name
PROGRESS_FILE = ".extract_progress.json"


class ExtractionError(Exception):
    """Custom exception for extraction errors with recovery info."""
    def __init__(self, message: str, temp_file: Optional[Path] = None, 
                 target_dir: Optional[Path] = None):
        super().__init__(message)
        self.temp_file = temp_file
        self.target_dir = target_dir


def _shorten_path(long_path: Path, max_length: int = 200) -> Path:
    """
    Shorten a path if it exceeds Windows path limit.
    Uses MD5 hash of the original name to create a shorter unique name.
    """
    path_str = str(long_path)
    if len(path_str) <= max_length:
        return long_path
    
    parent = long_path.parent
    stem = long_path.stem
    suffix = long_path.suffix
    
    hash_suffix = hashlib.md5(stem.encode()).hexdigest()[:8]
    short_stem = stem[:50] + "_" + hash_suffix
    
    short_path = parent / (short_stem + suffix)
    logger.info(f"[marker] Shortened path: {long_path.name} -> {short_path.name}")
    return short_path


def _ensure_dir_exists(dir_path: Path) -> Path:
    """
    Ensure directory exists, with fallback for path length issues.
    Returns the actual directory path used.
    """
    if len(str(dir_path)) > 240:
        parent = dir_path.parent
        short_name = hashlib.md5(dir_path.name.encode()).hexdigest()[:12]
        dir_path = parent / short_name
        logger.info(f"[marker] Using shorter directory name: {dir_path}")
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    except OSError as e:
        logger.error(f"[marker] Failed to create directory: {e}")
        raise


def write_progress(
    progress_dir: Path,
    status: str,
    progress: int,
    message: str,
    current_step: Optional[str] = None,
    pid: Optional[int] = None
) -> None:
    """
    Write extraction progress to a JSON file for persistence.
    
    Args:
        progress_dir: Directory to write progress file
        status: One of 'idle', 'extracting', 'splitting', 'completed', 'error', 'cancelled'
        progress: Progress percentage (0-100)
        message: Human-readable status message
        current_step: Current processing step name
        pid: Process ID of the extraction process
    """
    progress_file = progress_dir / PROGRESS_FILE
    
    data = {
        "status": status,
        "progress": progress,
        "message": message,
        "current_step": current_step,
        "pid": pid or os.getpid(),
        "updated_at": datetime.now().isoformat(),
    }
    
    try:
        progress_dir.mkdir(parents=True, exist_ok=True)
        progress_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        logger.warning(f"[marker] Failed to write progress: {e}")


def read_progress(progress_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Read extraction progress from JSON file.
    
    Args:
        progress_dir: Directory containing progress file
        
    Returns:
        Progress dict or None if not found or empty
    """
    progress_file = progress_dir / PROGRESS_FILE
    
    if not progress_file.exists():
        return None
    
    try:
        content = progress_file.read_text(encoding='utf-8').strip()
        if not content:
            # File exists but is empty (being written)
            return None
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        # File is being written, will retry next poll
        return None
    except Exception as e:
        logger.warning(f"[marker] Failed to read progress: {e}")
        return None


def clear_progress(progress_dir: Path) -> None:
    """Remove progress file."""
    progress_file = progress_dir / PROGRESS_FILE
    if progress_file.exists():
        try:
            progress_file.unlink()
        except Exception as e:
            logger.warning(f"[marker] Failed to clear progress: {e}")


def extract_pdf_with_marker(
    pdf_path: Path,
    output_dir: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[Path, Optional[Path]]:
    """
    Extract PDF to Markdown using marker-pdf (OCR-based).
    
    Progress is written to {output_dir}/.extract_progress.json for persistence.
    
    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save the output markdown and images
        progress_callback: Optional callback(progress_percent, message)
        
    Returns:
        Tuple of (output_md_path, temp_file_path)
        - If successful, temp_file_path is None
        - If copy failed, temp_file_path contains the temp file location
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ExtractionError: If extraction fails (with recovery info)
    """
    logger.info(f"[marker] Starting extraction: {pdf_path}")
    temp_md_path = None
    
    # Ensure output dir exists for progress file
    output_dir.mkdir(parents=True, exist_ok=True)
    
    def update_progress(pct: int, msg: str, step: Optional[str] = None):
        """Update both callback and progress file."""
        write_progress(output_dir, 'extracting', pct, msg, step)
        if progress_callback:
            progress_callback(pct, msg)
    
    if not pdf_path.exists():
        write_progress(output_dir, 'error', 0, f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Create new event loop for this thread
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("[marker] Created new event loop for worker thread")
    
    # Report progress: initializing
    update_progress(5, "Loading marker-pdf models...", "Loading Models")
    
    try:
        # Import marker-pdf (lazy import to avoid slow startup)
        logger.info("[marker] Importing marker-pdf library...")
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.config.parser import ConfigParser
        
        update_progress(10, "Initializing OCR models...", "Loading Models")
        
        # Create configuration
        logger.info("[marker] Creating configuration...")
        config_parser = ConfigParser({
            "output_format": "markdown",
            "force_ocr": False,
            "paginate_output": False,
        })
        
        # Load models
        logger.info("[marker] Loading models...")
        update_progress(15, "Loading OCR and layout models...", "Loading Models")
        
        model_dict = create_model_dict()
        
        update_progress(20, "Models loaded, creating converter...", "Initializing")
        
        # Create converter
        logger.info("[marker] Creating PDF converter...")
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=model_dict,
        )
        
        update_progress(25, "Processing PDF pages...", "Processing")
        
        # Create a tqdm interceptor to capture progress stages
        # marker-pdf uses tqdm.auto, so we need to patch both
        import tqdm
        import tqdm.auto
        original_tqdm = tqdm.tqdm
        original_auto_tqdm = tqdm.auto.tqdm
        
        # Stage progress mapping
        stage_progress = {
            "Recognizing Layout": (25, 45),
            "Running OCR Error Detection": (45, 55),
            "Detecting bboxes": (55, 65),
            "Recognizing Text": (65, 75),
            "Recognizing tables": (75, 85),
        }
        current_stage = {"name": "Processing", "start": 25, "end": 45}
        
        class TqdmProgressCapture(original_tqdm):
            """Wrapper to capture tqdm progress and relay to our callback."""
            def __init__(self, *args, **kwargs):
                desc = kwargs.get('desc', '') or (args[0] if args and isinstance(args[0], str) else '')
                if not desc and 'iterable' in kwargs:
                    desc = str(kwargs.get('desc', ''))
                
                for stage_name, (start, end) in stage_progress.items():
                    if stage_name in str(desc):
                        current_stage["name"] = stage_name
                        current_stage["start"] = start
                        current_stage["end"] = end
                        update_progress(start, f"{stage_name}...", stage_name)
                        logger.info(f"[marker] Stage: {stage_name}")
                        break
                
                super().__init__(*args, **kwargs)
            
            def update(self, n=1):
                result = super().update(n)
                if self.total and self.n % 10 == 0:  # Log every 10 iterations
                    stage_pct = self.n / self.total
                    overall_pct = int(current_stage["start"] + 
                                     stage_pct * (current_stage["end"] - current_stage["start"]))
                    logger.info(f"[marker] TqdmCapture update: {self.n}/{self.total} -> {overall_pct}%")
                    update_progress(
                        overall_pct, 
                        f"{current_stage['name']}: {self.n}/{self.total}",
                        current_stage['name']
                    )
                return result
        
        # Monkey-patch both tqdm and tqdm.auto
        tqdm.tqdm = TqdmProgressCapture
        tqdm.auto.tqdm = TqdmProgressCapture
        
        try:
            logger.info(f"[marker] Converting PDF: {pdf_path.name}")
            rendered = converter(str(pdf_path))
        finally:
            # Restore original tqdm
            tqdm.tqdm = original_tqdm
            tqdm.auto.tqdm = original_auto_tqdm
        
        update_progress(85, "Saving markdown output...", "Saving")
        
        # Get markdown content
        markdown_content = rendered.markdown
        
        # Save to temp file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', 
                                          encoding='utf-8', delete=False) as tmp:
            tmp.write(markdown_content)
            temp_md_path = Path(tmp.name)
        
        logger.info(f"[marker] Saved to temp file: {temp_md_path}")
        
        # Try to create output directory
        try:
            actual_output_dir = _ensure_dir_exists(output_dir)
        except OSError as e:
            write_progress(output_dir, 'error', 85, 
                          f"Failed to create output directory: {e}\nTemp file saved: {temp_md_path}")
            raise ExtractionError(
                f"Failed to create output directory: {e}\nTemp file saved: {temp_md_path}",
                temp_file=temp_md_path,
                target_dir=output_dir
            )
        
        # Determine output file path
        output_md_path = actual_output_dir / f"{pdf_path.stem}.md"
        output_md_path = _shorten_path(output_md_path)
        
        update_progress(90, "Copying to output location...", "Saving")
        
        logger.info(f"[marker] Copying to: {output_md_path}")
        
        try:
            shutil.copy2(temp_md_path, output_md_path)
            temp_md_path.unlink()
            temp_md_path = None
        except OSError as e:
            write_progress(output_dir, 'error', 90,
                          f"Failed to copy file: {e}\nTemp file location: {temp_md_path}")
            raise ExtractionError(
                f"Failed to copy file: {e}\nTemp file location: {temp_md_path}\nTarget location: {output_md_path}",
                temp_file=temp_md_path,
                target_dir=actual_output_dir
            )
        
        # Save images if any
        if rendered.images:
            update_progress(95, f"Saving {len(rendered.images)} images...", "Saving Images")
            
            images_dir = actual_output_dir / "images"
            images_dir.mkdir(exist_ok=True)
            logger.info(f"[marker] Saving {len(rendered.images)} images...")
            
            for img_name, img in rendered.images.items():
                img_path = images_dir / img_name
                try:
                    img.save(str(img_path))
                except Exception as img_err:
                    logger.warning(f"[marker] Failed to save image {img_name}: {img_err}")
        
        # Mark as completed (but not done with splitting yet)
        update_progress(100, "PDF extraction completed!", "Extraction Done")
        
        logger.info(f"[marker] Extraction completed: {output_md_path}")
        return output_md_path, None
        
    except ImportError as e:
        logger.error(f"[marker] Failed to import marker-pdf: {e}")
        write_progress(output_dir, 'error', 0, "marker-pdf not installed. Run: pip install marker-pdf")
        raise RuntimeError(
            "marker-pdf not installed. Run: pip install marker-pdf"
        ) from e
    except ExtractionError:
        raise
    except Exception as e:
        logger.error(f"[marker] Extraction failed: {e}")
        error_msg = f"PDF extraction failed: {str(e)}"
        if temp_md_path and temp_md_path.exists():
            error_msg += f"\nTemp file saved: {temp_md_path}"
            write_progress(output_dir, 'error', 0, error_msg)
            raise ExtractionError(error_msg, temp_file=temp_md_path, target_dir=output_dir)
        write_progress(output_dir, 'error', 0, error_msg)
        raise RuntimeError(f"PDF extraction failed: {str(e)}") from e


def copy_temp_to_output(temp_file: Path, output_dir: Path, filename: str) -> Path:
    """
    Manually copy temp file to output directory.
    Used for recovery when automatic copy fails.
    """
    actual_output_dir = _ensure_dir_exists(output_dir)
    output_path = actual_output_dir / filename
    output_path = _shorten_path(output_path)
    
    shutil.copy2(temp_file, output_path)
    temp_file.unlink()
    
    return output_path


def is_scanned_pdf(pdf_path: Path) -> bool:
    """Check if a PDF is scanned (image-based) or has extractable text."""
    try:
        import fitz
        
        doc = fitz.open(str(pdf_path))
        total_text = ""
        
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            total_text += page.get_text()
        
        doc.close()
        
        avg_chars = len(total_text) / min(3, len(doc)) if doc else 0
        is_scanned = avg_chars < 100
        
        logger.info(f"[marker] PDF scan check: {pdf_path.name}, avg_chars={avg_chars:.0f}, is_scanned={is_scanned}")
        return is_scanned
        
    except Exception as e:
        logger.warning(f"[marker] Could not check if PDF is scanned: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python marker_extract.py <pdf_path>")
        sys.exit(1)
    
    pdf = Path(sys.argv[1])
    output = pdf.parent / pdf.stem
    
    def progress(pct, msg):
        print(f"[{pct:3d}%] {msg}")
    
    result, temp = extract_pdf_with_marker(pdf, output, progress)
    print(f"Output: {result}")
    if temp:
        print(f"Temp file (needs manual copy): {temp}")
