#!/usr/bin/env python
"""
PDF Extraction Worker Script.

This script runs as a separate process to extract PDF to Markdown.
Progress is written to a JSON file for the main process to read.

Uses a tqdm output parser to capture real-time progress.

Usage:
    python extract_worker.py <pdf_path> <output_dir>
"""

import sys
import os
import re
import logging
import json
import threading
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent))  # backend dir
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root (for split_markdown)

# Progress file name (must match marker_extract.py)
PROGRESS_FILE = ".extract_progress.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def write_worker_progress(progress_dir: Path, status: str, progress: int, 
                          message: str, current_step: str = None, pid: int = None,
                          md_file: str = None):
    """Write progress to JSON file."""
    progress_file = progress_dir / PROGRESS_FILE
    
    # Read existing data to preserve md_file if not specified
    existing_md_file = None
    if progress_file.exists():
        try:
            existing = json.loads(progress_file.read_text(encoding='utf-8'))
            existing_md_file = existing.get('md_file')
        except:
            pass
    
    data = {
        "status": status,
        "progress": progress,
        "message": message,
        "current_step": current_step,
        "pid": pid or os.getpid(),
        "updated_at": datetime.now().isoformat(),
        "md_file": md_file or existing_md_file  # Preserve md_file for resume
    }
    try:
        progress_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f"[Worker] Failed to write progress: {e}", file=sys.stderr)


def _save_md_file_for_resume(progress_dir: Path, md_output: Path):
    """Save md_file path to progress file for resume support."""
    progress_file = progress_dir / PROGRESS_FILE
    try:
        data = json.loads(progress_file.read_text(encoding='utf-8'))
        data['md_file'] = str(md_output)
        progress_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f"[Worker] Failed to save md_file for resume: {e}", file=sys.stderr)


# Stage progress mapping
STAGE_PROGRESS = {
    "Recognizing Layout": (25, 45),
    "Running OCR": (45, 55),
    "Detecting bboxes": (55, 65),
    "Recognizing Text": (65, 75),
    "Recognizing tables": (75, 85),
}


class TqdmOutputParser:
    """Parse tqdm output to extract progress."""
    
    # Pattern to match tqdm output like: "Stage Name: 50%|...|25/50 [...]"
    TQDM_PATTERN = re.compile(r'([^:]+):\s*(\d+)%\|[^|]*\|\s*(\d+)/(\d+)')
    
    def __init__(self, output_dir: Path, pid: int):
        self.output_dir = output_dir
        self.pid = pid
        self.current_stage = "Processing"
        self.last_progress = 0
    
    def parse_line(self, line: str):
        """Parse a line of output for tqdm progress."""
        match = self.TQDM_PATTERN.search(line)
        if match:
            stage_name = match.group(1).strip()
            percent = int(match.group(2))
            current = int(match.group(3))
            total = int(match.group(4))
            
            # Find the stage in our mapping
            for stage, (start, end) in STAGE_PROGRESS.items():
                if stage in stage_name:
                    stage_pct = current / total if total > 0 else 0
                    overall_pct = int(start + stage_pct * (end - start))
                    
                    # Always update progress (every 5 items to reduce file writes)
                    if current % 5 == 0 or current == total:
                        print(f"[Worker] Parsed: {stage} {current}/{total} -> {overall_pct}%", file=sys.__stderr__)
                        self.last_progress = overall_pct
                        self.current_stage = stage
                        write_worker_progress(
                            self.output_dir, 'extracting', overall_pct,
                            f"{stage}: {current}/{total}",
                            stage, self.pid
                        )
                    break


class TeeStderr:
    """Tee stderr to both console and a parser."""
    
    def __init__(self, parser: TqdmOutputParser):
        self.parser = parser
        self.original_stderr = sys.__stderr__
        self.buffer = ""
    
    def write(self, text):
        # Write to original stderr
        if self.original_stderr:
            self.original_stderr.write(text)
            self.original_stderr.flush()
        
        # Parse for tqdm output
        self.buffer += text
        while '\r' in self.buffer or '\n' in self.buffer:
            # Split on newline or carriage return
            if '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
            elif '\r' in self.buffer:
                line, self.buffer = self.buffer.split('\r', 1)
            else:
                break
            
            if line.strip():
                self.parser.parse_line(line)
    
    def flush(self):
        if self.original_stderr:
            self.original_stderr.flush()


def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_worker.py <pdf_path> <output_dir>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    current_pid = os.getpid()
    
    logger.info(f"[Worker] Starting extraction: {pdf_path}")
    logger.info(f"[Worker] Output dir: {output_dir}")
    logger.info(f"[Worker] PID: {current_pid}")
    
    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up stderr tee to parse tqdm output
    parser = TqdmOutputParser(output_dir, current_pid)
    tee_stderr = TeeStderr(parser)
    sys.stderr = tee_stderr
    
    try:
        # Check if we can resume from a previous extraction BEFORE importing heavy marker libraries
        from marker_extract import read_progress
        
        logger.info(f"[Worker] Checking for resume at: {output_dir}")
        existing_progress = read_progress(output_dir)
        logger.info(f"[Worker] Existing progress: {existing_progress}")
        md_output = None
        
        if existing_progress and existing_progress.get('status') == 'extracted':
            # Resume from split step - skip marker-pdf loading
            md_file = existing_progress.get('md_file')
            logger.info(f"[Worker] Found extracted status, md_file: {md_file}")
            if md_file:
                md_output = Path(md_file)
                if md_output.exists():
                    logger.info(f"[Worker] Resuming from split step (skipping marker-pdf), MD file: {md_output}")
                else:
                    logger.warning(f"[Worker] MD file not found, need full extraction: {md_file}")
                    md_output = None
        else:
            logger.info(f"[Worker] No resume: status is {existing_progress.get('status') if existing_progress else 'None'}")
        
        if md_output is None:
            # Need full extraction - import heavy marker-pdf library
            logger.info("[Worker] Importing marker-pdf for full extraction...")
            from marker_extract import extract_pdf_with_marker
            
            # Write initial progress only if not resuming
            write_worker_progress(output_dir, 'extracting', 0, 'Starting extraction...', 'Starting', current_pid)
            
            # Progress callback for non-tqdm progress
            def progress_callback(pct: int, msg: str):
                write_worker_progress(output_dir, 'extracting', pct, msg, 
                                     msg.split(':')[0] if ':' in msg else msg, current_pid)
            
            # Run extraction
            md_output, temp_file = extract_pdf_with_marker(pdf_path, output_dir, progress_callback)
            
            if temp_file:
                write_worker_progress(output_dir, 'error', 0, 
                              f'Extraction succeeded but save failed. Temp file: {temp_file}', 'Error')
                logger.error(f"[Worker] Extraction failed: temp file at {temp_file}")
                sys.exit(1)
            
            logger.info(f"[Worker] Extraction completed: {md_output}")
            
            # Mark as extracted (PDF done, split pending) - save md_file for resume
            write_worker_progress(output_dir, 'extracted', 80, 
                          f'PDF extraction completed: {md_output.name}', 'Extracted', current_pid)
            # Also save md_file path for resume
            _save_md_file_for_resume(output_dir, md_output)
        
        # Fix image paths before splitting
        from fix_markdown_images import fix_image_paths
        fix_count = fix_image_paths(md_output)
        logger.info(f"[Worker] Fixed {fix_count} image paths")
        
        # Split into chapters
        write_worker_progress(output_dir, 'splitting', 85, 'Splitting into chapters...', 'Splitting', current_pid)
        
        from split_markdown import split_markdown_file
        split_markdown_file(md_output, output_dir)
        
        # Count chapters
        chapter_count = len([f for f in output_dir.glob('*.md') if f.name != md_output.name])
        
        # Mark as completed
        write_worker_progress(output_dir, 'completed', 100, 
                      f'Extraction completed! Created {chapter_count} chapters.', 'Completed')
        
        logger.info(f"[Worker] Done! Created {chapter_count} chapters")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"[Worker] Extraction failed: {e}")
        write_worker_progress(output_dir, 'error', 0, f'Extraction failed: {str(e)}', 'Error')
        sys.exit(1)
    finally:
        sys.stderr = sys.__stderr__


if __name__ == '__main__':
    main()
