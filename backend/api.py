"""
API routes for the AI-Readwise application.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from typing import List
import asyncio
import json

from .models import Book, Chapter, BookDetail, ExtractProgress, ExtractResult
from .services import BookService, ExtractService
from .translation_service import translation_service, LANG_ZH, LANG_EN
from .summary_service import summary_service

# Get resources directory
RESOURCES_DIR = Path(__file__).parent.parent / "resources"

# Initialize services
book_service = BookService(RESOURCES_DIR)
extract_service = ExtractService(RESOURCES_DIR)

# Create router
router = APIRouter(prefix="/api", tags=["books"])


@router.get("/books", response_model=List[Book])
async def get_books():
    """Get all books."""
    return book_service.get_all_books()


@router.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    """Get a specific book."""
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/books/{book_id}/chapters", response_model=List[Chapter])
async def get_chapters(book_id: str):
    """Get all chapters of a book."""
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_service.get_chapters(book_id)


@router.get("/books/{book_id}/chapters/{chapter_filename}")
async def get_chapter_content(book_id: str, chapter_filename: str):
    """Get the content of a specific chapter."""
    content = book_service.get_chapter_content(book_id, chapter_filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"content": content}


@router.get("/books/{book_id}/images/{image_path:path}")
async def get_book_image(book_id: str, image_path: str):
    """Serve an image from a book's directory."""
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get the chapter directory (same as pdf stem)
    book_dir = RESOURCES_DIR / book_id
    chapter_dir = book_dir / Path(book.file).stem
    image_file = chapter_dir / image_path
    
    if not image_file.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine media type
    suffix = image_file.suffix.lower()
    media_types = {
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    media_type = media_types.get(suffix, 'application/octet-stream')
    
    return FileResponse(image_file, media_type=media_type)


@router.post("/books/{book_id}/extract")
async def extract_book(book_id: str):
    """
    Extract PDF to markdown chapters with SSE progress updates.
    Returns a Server-Sent Events stream.
    """
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.has_chapters:
        raise HTTPException(status_code=400, detail="Book already has chapters")
    
    async def event_stream():
        progress_queue = asyncio.Queue()
        
        def progress_callback(progress: ExtractProgress):
            asyncio.get_event_loop().call_soon_threadsafe(
                progress_queue.put_nowait, progress
            )
        
        # Start extraction in background
        extract_task = asyncio.create_task(
            extract_service.extract_pdf(book_id, progress_callback)
        )
        
        # Stream progress updates
        while not extract_task.done():
            try:
                progress = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                yield f"data: {json.dumps(progress.model_dump())}\n\n"
            except asyncio.TimeoutError:
                continue
        
        # Drain remaining progress updates
        while not progress_queue.empty():
            progress = await progress_queue.get()
            yield f"data: {json.dumps(progress.model_dump())}\n\n"
        
        # Send final result
        success = extract_task.result()
        final_progress = extract_service.get_extraction_status(book_id)
        if final_progress:
            yield f"data: {json.dumps(final_progress.model_dump())}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/books/{book_id}/extract/status", response_model=ExtractProgress)
async def get_extract_status(book_id: str):
    """
    Get current extraction status from persisted progress file.
    This allows checking status even after page navigation.
    """
    progress = extract_service.get_extraction_status(book_id)
    if not progress:
        return ExtractProgress(
            status="idle",
            progress=0,
            message="No extraction in progress"
        )
    return progress


@router.post("/books/{book_id}/extract/cancel")
async def cancel_extraction(book_id: str):
    """
    Cancel an ongoing extraction.
    Kills the extraction process and updates status.
    """
    success = extract_service.cancel_extraction(book_id)
    if not success:
        raise HTTPException(status_code=400, detail="No extraction to cancel or cancel failed")
    return {"success": True, "message": "Extraction cancelled"}


@router.get("/books/{book_id}/source")
async def get_source_markdown(book_id: str):
    """
    Get the original (source) markdown file content.
    This is the full document before chapter splitting.
    """
    content = book_service.get_source_markdown(book_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Source markdown not found")
    return {"content": content}


@router.put("/books/{book_id}/source")
async def update_source_markdown(book_id: str, body: dict):
    """
    Update the source markdown file content.
    Used for editing/proofreading before re-splitting.
    """
    content = body.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="Content is required")
    
    success = book_service.update_source_markdown(book_id, content)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"success": True, "message": "Source markdown updated"}


@router.post("/books/{book_id}/resplit")
async def resplit_chapters(book_id: str):
    """
    Re-split the source markdown into chapters.
    This will delete existing chapter files and regenerate them.
    """
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    try:
        # Delete existing chapters and re-split
        chapter_count = book_service.resplit_chapters(book_id)
        return {
            "success": True,
            "message": f"Successfully re-split into {chapter_count} chapters",
            "chapter_count": chapter_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Translation Endpoints =============

@router.get("/config/models")
async def get_available_models():
    """Get list of available LLM models for translation."""
    return {
        "models": translation_service.get_available_models(),
        "default": translation_service.get_default_model()
    }


@router.get("/books/{book_id}/languages")
async def get_book_languages(book_id: str):
    """
    Get language information for a book.
    Returns detected source language and available translations.
    """
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    try:
        result = book_service.get_language_info(book_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/translate")
async def translate_book(book_id: str, target_lang: str, model: str):
    """
    Translate book to target language with SSE progress updates.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if target_lang not in [LANG_ZH, LANG_EN]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target_lang}")
    
    logger.info(f"[API] Starting translation: book={book_id}, target={target_lang}, model={model}")
    
    async def event_stream():
        progress_queue = asyncio.Queue()
        # Capture the event loop BEFORE starting the thread
        loop = asyncio.get_running_loop()
        
        def progress_callback(pct: int, msg: str):
            # Use the captured loop reference
            loop.call_soon_threadsafe(
                progress_queue.put_nowait,
                {"progress": pct, "message": msg}
            )
        
        # Run translation in thread pool
        import concurrent.futures
        logger.info(f"[API] Creating thread pool for translation")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                book_service.translate_book,
                book_id, target_lang, model, progress_callback
            )
            
            while not future.done():
                try:
                    progress = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    yield f"data: {json.dumps(progress)}\n\n"
                except asyncio.TimeoutError:
                    pass
            
            # Get result or raise exception
            try:
                result = future.result()
                logger.info(f"[API] Translation completed: {result} chapters")
                yield f"data: {json.dumps({'status': 'completed', 'chapter_count': result})}\n\n"
            except Exception as e:
                logger.exception(f"[API] Translation failed: {e}")
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/books/{book_id}/translate/cancel")
async def cancel_translation(book_id: str):
    """Cancel ongoing translation for a book."""
    import logging
    logger = logging.getLogger(__name__)
    
    translation_service.cancel_translation(book_id)
    logger.info(f"[API] Translation cancellation requested for: {book_id}")
    
    return {"success": True, "message": "Cancellation requested"}


@router.get("/books/{book_id}/chapters/{lang}")
async def get_translated_chapters(book_id: str, lang: str):
    """Get chapters for a specific language version."""
    book = book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    chapters = book_service.get_chapters_for_lang(book_id, lang)
    return chapters


@router.get("/books/{book_id}/chapters/{lang}/{chapter_filename}")
async def get_translated_chapter_content(book_id: str, lang: str, chapter_filename: str):
    """Get content of a chapter in specific language."""
    content = book_service.get_chapter_content_for_lang(book_id, lang, chapter_filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"content": content}


# ============ Summary Endpoints ============

@router.get("/books/{book_id}/chapters/{lang}/{chapter_filename}/summary")
async def get_chapter_summary(book_id: str, lang: str, chapter_filename: str):
    """Get existing summary for a chapter."""
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language not found")
    
    summary = summary_service.get_summary(chapter_dir, chapter_filename)
    has_mp3 = summary_service.get_mp3_path(chapter_dir, chapter_filename) is not None
    return {"summary": summary, "has_mp3": has_mp3}


@router.post("/books/{book_id}/chapters/{lang}/{chapter_filename}/summary")
async def generate_chapter_summary(
    book_id: str, 
    lang: str, 
    chapter_filename: str,
    model: str = None
):
    """Generate a new summary for a chapter using LLM."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get chapter content
    content = book_service.get_chapter_content_for_lang(book_id, lang, chapter_filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Get chapter dir for storage
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language directory not found")
    
    # Extract chapter title from filename or content
    chapter_title = chapter_filename.replace(".md", "").replace("_", " ")
    # Try to get from first heading in content
    for line in content.split("\n")[:10]:
        if line.startswith("# "):
            chapter_title = line[2:].strip()
            break
    
    # Detect domain (simple heuristic from book name)
    book = book_service.get_book(book_id)
    domain = "general knowledge"
    if book:
        # Use book title as hint for domain
        title_lower = book.title.lower()
        if any(kw in title_lower for kw in ["data", "software", "system", "computer", "programming"]):
            domain = "software engineering"
        elif any(kw in title_lower for kw in ["business", "management", "marketing"]):
            domain = "business and management"
        elif any(kw in title_lower for kw in ["science", "physics", "chemistry", "biology"]):
            domain = "natural sciences"
    
    try:
        # Delete existing MP3 when regenerating summary
        summary_service.delete_mp3(chapter_dir, chapter_filename)
        
        # Generate summary
        summary_data = summary_service.generate_summary(
            chapter_content=content,
            chapter_title=chapter_title,
            domain=domain,
            target_lang=lang,
            model=model
        )
        
        # Save to file
        summary_service.save_summary(chapter_dir, chapter_filename, summary_data)
        
        return {"summary": summary_data, "success": True, "has_mp3": False}
        
    except Exception as e:
        logger.error(f"[API] Summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.put("/books/{book_id}/chapters/{lang}/{chapter_filename}/summary")
async def update_chapter_summary(
    book_id: str,
    lang: str,
    chapter_filename: str,
    summary_data: dict
):
    """Update/save edited summary for a chapter."""
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language directory not found")
    
    # Preserve metadata
    existing = summary_service.get_summary(chapter_dir, chapter_filename)
    if existing:
        summary_data["generated_at"] = existing.get("generated_at")
        summary_data["domain"] = existing.get("domain")
        summary_data["model"] = existing.get("model")
        summary_data["chapter_title"] = existing.get("chapter_title")
    
    summary_data["edited_at"] = __import__("datetime").datetime.now().isoformat()
    
    success = summary_service.save_summary(chapter_dir, chapter_filename, summary_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save summary")
    
    return {"success": True, "summary": summary_data}


@router.post("/books/{book_id}/chapters/{lang}/{chapter_filename}/summary/mp3")
async def generate_summary_mp3(book_id: str, lang: str, chapter_filename: str):
    """Generate MP3 from voice script."""
    import logging
    logger = logging.getLogger(__name__)
    
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language directory not found")
    
    # Get existing summary
    summary = summary_service.get_summary(chapter_dir, chapter_filename)
    if not summary or not summary.get("voice_script"):
        raise HTTPException(status_code=400, detail="No voice script found. Generate summary first.")
    
    try:
        mp3_path = await summary_service.generate_mp3(
            chapter_dir=chapter_dir,
            chapter_filename=chapter_filename,
            voice_script=summary["voice_script"],
            lang=lang
        )
        
        if mp3_path:
            return {"success": True, "has_mp3": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate MP3")
            
    except Exception as e:
        logger.error(f"[API] MP3 generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"MP3 generation failed: {str(e)}")


@router.get("/books/{book_id}/chapters/{lang}/{chapter_filename}/summary/mp3")
async def get_summary_mp3(book_id: str, lang: str, chapter_filename: str):
    """Get MP3 file for voice script."""
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language directory not found")
    
    mp3_path = summary_service.get_mp3_path(chapter_dir, chapter_filename)
    if not mp3_path:
        raise HTTPException(status_code=404, detail="MP3 not found. Generate it first.")
    
    return FileResponse(
        path=str(mp3_path),
        media_type="audio/mpeg",
        filename=mp3_path.name
    )


@router.get("/books/{book_id}/summaries/{lang}/status")
async def get_all_summaries_status(book_id: str, lang: str):
    """Get summary and MP3 status for all chapters."""
    chapters = book_service.get_chapters_for_lang(book_id, lang)
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language not found")
    
    result = []
    with_summary = 0
    with_mp3 = 0
    
    for ch in chapters:
        has_summary = summary_service.get_summary(chapter_dir, ch.filename) is not None
        has_mp3 = summary_service.get_mp3_path(chapter_dir, ch.filename) is not None
        
        if has_summary:
            with_summary += 1
        if has_mp3:
            with_mp3 += 1
            
        result.append({
            "filename": ch.filename,
            "title": ch.name,
            "has_summary": has_summary,
            "has_mp3": has_mp3
        })
    
    return {
        "chapters": result,
        "total": len(result),
        "with_summary": with_summary,
        "with_mp3": with_mp3
    }


@router.post("/books/{book_id}/summaries/{lang}/generate-all")
async def generate_all_summaries(book_id: str, lang: str, model: str = None):
    """Generate summaries and MP3 for all chapters (SSE)."""
    import logging
    logger = logging.getLogger(__name__)
    
    chapters = book_service.get_chapters_for_lang(book_id, lang)
    chapter_dir = book_service.get_chapter_dir(book_id, lang)
    
    if not chapter_dir:
        raise HTTPException(status_code=404, detail="Book or language not found")
    
    # Get book for domain detection
    book = book_service.get_book(book_id)
    domain = "general knowledge"
    if book:
        title_lower = book.title.lower()
        if any(kw in title_lower for kw in ["data", "software", "system", "computer", "programming"]):
            domain = "software engineering"
        elif any(kw in title_lower for kw in ["business", "management", "marketing"]):
            domain = "business and management"
    
    async def generate():
        total = len(chapters)
        generated_summaries = 0
        generated_mp3s = 0
        
        for idx, ch in enumerate(chapters):
            current = idx + 1
            
            # Check if summary exists
            existing_summary = summary_service.get_summary(chapter_dir, ch.filename)
            
            if not existing_summary:
                # Generate summary
                yield f"data: {json.dumps({'type': 'progress', 'current': current, 'total': total, 'chapter': ch.filename, 'step': 'summary'})}\n\n"
                
                try:
                    content = book_service.get_chapter_content_for_lang(book_id, lang, ch.filename)
                    if content:
                        chapter_title = ch.name
                        summary_data = summary_service.generate_summary(
                            chapter_content=content,
                            chapter_title=chapter_title,
                            domain=domain,
                            target_lang=lang,
                            model=model
                        )
                        summary_service.save_summary(chapter_dir, ch.filename, summary_data)
                        generated_summaries += 1
                        existing_summary = summary_data
                except Exception as e:
                    logger.error(f"[Batch] Failed to generate summary for {ch.filename}: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'chapter': ch.filename, 'step': 'summary', 'message': str(e)})}\n\n"
                    continue
            
            # Check if MP3 exists
            if not summary_service.get_mp3_path(chapter_dir, ch.filename):
                # Generate MP3
                yield f"data: {json.dumps({'type': 'progress', 'current': current, 'total': total, 'chapter': ch.filename, 'step': 'mp3'})}\n\n"
                
                voice_script = existing_summary.get("voice_script") if existing_summary else None
                if voice_script:
                    try:
                        await summary_service.generate_mp3(
                            chapter_dir=chapter_dir,
                            chapter_filename=ch.filename,
                            voice_script=voice_script,
                            lang=lang
                        )
                        generated_mp3s += 1
                    except Exception as e:
                        logger.error(f"[Batch] Failed to generate MP3 for {ch.filename}: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'chapter': ch.filename, 'step': 'mp3', 'message': str(e)})}\n\n"
            
            # Small delay to allow UI updates
            await asyncio.sleep(0.1)
        
        yield f"data: {json.dumps({'type': 'complete', 'generated_summaries': generated_summaries, 'generated_mp3s': generated_mp3s})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
