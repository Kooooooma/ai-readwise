#!/usr/bin/env python3
"""
PDF to Markdown Converter

This script converts PDF files to Markdown format using pymupdf4llm.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import pymupdf4llm


def convert_pdf_to_markdown(
    pdf_path: Path,
    output_path: Optional[Path] = None,
    page_chunks: bool = False,
) -> None:
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path for the output Markdown file (optional)
        page_chunks: If True, text is returned page-by-page (default: False)

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the PDF file is invalid
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")

    # Determine output path
    if output_path is None:
        output_path = pdf_path.with_suffix(".md")

    print(f"Converting: {pdf_path}")
    print(f"Output to: {output_path}")

    # Convert PDF to Markdown
    try:
        markdown_text = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=page_chunks,
        )

        # Write to file
        output_path.write_text(markdown_text, encoding="utf-8")
        print(f"✓ Conversion successful!")

    except Exception as e:
        raise ValueError(f"Failed to convert PDF: {e}") from e


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "pdf_file",
        type=Path,
        help="Path to the PDF file to convert",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output Markdown file path (default: same name as PDF with .md extension)",
    )

    parser.add_argument(
        "--page-chunks",
        action="store_true",
        help="Process PDF page by page instead of as a whole document",
    )

    args = parser.parse_args()

    try:
        convert_pdf_to_markdown(
            pdf_path=args.pdf_file,
            output_path=args.output,
            page_chunks=args.page_chunks,
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
