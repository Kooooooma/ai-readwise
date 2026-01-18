#!/usr/bin/env python3
"""
Markdown Document Splitter

This script splits a Markdown file into multiple sub-documents based on 
top-level headings (lines starting with a single '#').
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def parse_markdown(content: str) -> List[Tuple[str, str]]:
    """
    Parse markdown content and split by top-level headings.
    
    Args:
        content: The markdown file content
        
    Returns:
        List of tuples containing (heading_text, section_content)
    """
    sections = []
    lines = content.split('\n')
    
    current_heading = None
    current_content = []
    
    for line in lines:
        # Check if line is a top-level heading (starts with single #)
        if re.match(r'^#\s+', line):
            # Save previous section if exists
            if current_heading is not None:
                sections.append((current_heading, '\n'.join(current_content)))
            
            # Start new section
            current_heading = line[2:].strip()  # Remove '# ' prefix
            current_content = [line]  # Include the heading in content
        else:
            # Add line to current section
            if current_heading is not None:
                current_content.append(line)
            # If no heading yet, this is preamble content, skip it
            # or you could save it as a separate "intro" section
    
    # Don't forget the last section
    if current_heading is not None:
        sections.append((current_heading, '\n'.join(current_content)))
    
    return sections


def sanitize_filename(text: str) -> str:
    """
    Convert heading text to a safe filename.
    
    Args:
        text: The heading text
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid filename characters
    # Keep Chinese characters, letters, numbers, spaces, and basic punctuation
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = text.strip()
    
    # Limit length to avoid filesystem issues
    if len(text) > 100:
        text = text[:100]
    
    return text


def split_markdown_file(
    input_file: Path,
    output_dir: Path = None,
) -> None:
    """
    Split a markdown file into multiple files based on top-level headings.
    
    Args:
        input_file: Path to the input markdown file
        output_dir: Optional output directory (default: same as input with input filename)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If input file is not a markdown file
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if input_file.suffix.lower() not in ['.md', '.markdown']:
        raise ValueError(f"Input file must be a markdown file: {input_file}")
    
    # Determine output directory
    if output_dir is None:
        # Create folder with same name as input file (without extension)
        output_dir = input_file.parent / input_file.stem
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Reading: {input_file}")
    
    # Read input file
    content = input_file.read_text(encoding='utf-8')
    
    # Parse and split
    sections = parse_markdown(content)
    
    if not sections:
        print("Warning: No top-level headings found in the document")
        return
    
    print(f"Found {len(sections)} sections")
    print(f"Output directory: {output_dir}")
    
    # Write each section to a separate file
    for idx, (heading, section_content) in enumerate(sections, 1):
        # Create filename from heading
        filename = sanitize_filename(heading)
        
        # Add index prefix to maintain order
        output_file = output_dir / f"{idx:02d}_{filename}.md"
        
        # Write file
        output_file.write_text(section_content, encoding='utf-8')
        print(f"  Created: {output_file.name}")
    
    print(f"\n✓ Successfully split into {len(sections)} files")


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Split Markdown file by top-level headings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the markdown file to split",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: folder named after input file)",
    )
    
    args = parser.parse_args()
    
    try:
        split_markdown_file(
            input_file=args.input_file,
            output_dir=args.output,
        )
        return 0
    
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
