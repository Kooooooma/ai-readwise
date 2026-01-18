"""
Fix image paths in markdown files.

This module provides a reusable function to fix image references in markdown files
that are extracted by marker-pdf. The images are stored in an 'images/' subdirectory
but the markdown references them without the directory prefix.
"""

import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Pattern to match image references that need fixing
# Matches: ![](_page_XX_...) or ![alt](_page_XX_...)
# Does NOT match: ![](images/_page_XX_...) (already fixed)
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\((?!images/)(_page_\d+[^)]+)\)')


def fix_image_paths(md_path: Path, images_dir: str = "images") -> int:
    """
    Fix image paths in a markdown file to use relative paths to the images directory.
    
    Replaces: ![](_page_XX_xxx.jpeg) -> ![](images/_page_XX_xxx.jpeg)
    
    Args:
        md_path: Path to the markdown file
        images_dir: Name of the images subdirectory (default: "images")
        
    Returns:
        Number of image paths fixed
    """
    if not md_path.exists():
        logger.warning(f"[ImageFix] Markdown file not found: {md_path}")
        return 0
    
    content = md_path.read_text(encoding='utf-8')
    
    # Count matches before replacement
    matches = IMAGE_PATTERN.findall(content)
    fix_count = len(matches)
    
    if fix_count == 0:
        logger.info(f"[ImageFix] No image paths to fix in: {md_path.name}")
        return 0
    
    # Replace image paths
    def replace_image(match):
        alt_text = match.group(1)
        image_name = match.group(2)
        return f'![{alt_text}]({images_dir}/{image_name})'
    
    fixed_content = IMAGE_PATTERN.sub(replace_image, content)
    
    # Write back
    md_path.write_text(fixed_content, encoding='utf-8')
    
    logger.info(f"[ImageFix] Fixed {fix_count} image paths in: {md_path.name}")
    return fix_count


def fix_image_paths_in_content(content: str, images_dir: str = "images") -> tuple[str, int]:
    """
    Fix image paths in markdown content string.
    
    Same as fix_image_paths but works on content directly instead of file.
    
    Args:
        content: Markdown content string
        images_dir: Name of the images subdirectory (default: "images")
        
    Returns:
        tuple[str, int]: (fixed_content, count_of_fixes)
    """
    matches = IMAGE_PATTERN.findall(content)
    fix_count = len(matches)
    
    if fix_count == 0:
        return content, 0
    
    def replace_image(match):
        alt_text = match.group(1)
        image_name = match.group(2)
        return f'![{alt_text}]({images_dir}/{image_name})'
    
    fixed_content = IMAGE_PATTERN.sub(replace_image, content)
    return fixed_content, fix_count
