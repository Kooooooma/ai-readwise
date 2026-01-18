#!/usr/bin/env python3
"""
Markdown to HTML Merger

This script merges multiple Markdown files from a directory into a single HTML page
with a fixed sidebar navigation and eye-friendly color scheme.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import markdown


# HTML template with fixed sidebar and eye-friendly colors
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            /* 护眼配色方案 - 类似 Solarized Light */
            --bg-main: #fdf6e3;           /* 温暖的米色背景 */
            --bg-sidebar: #eee8d5;        /* 侧边栏浅色背景 */
            --bg-nav-hover: #d3cbb7;      /* 导航悬停背景 */
            --text-primary: #586e75;      /* 主要文字颜色 */
            --text-heading: #073642;      /* 标题颜色 */
            --text-link: #268bd2;         /* 链接颜色 */
            --text-link-hover: #2aa198;   /* 链接悬停颜色 */
            --border-color: #93a1a1;      /* 边框颜色 */
            --code-bg: #eee8d5;           /* 代码背景 */
            --shadow: rgba(0, 0, 0, 0.1); /* 阴影颜色 */
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "Source Han Sans SC", sans-serif;
            line-height: 1.8;
            color: var(--text-primary);
            background-color: var(--bg-main);
            display: flex;
            min-height: 100vh;
        }}
        
        /* 固定侧边栏导航 */
        #sidebar {{
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            height: 100vh;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            padding: 2rem 1.5rem;
            box-shadow: 2px 0 8px var(--shadow);
        }}
        
        #sidebar h1 {{
            font-size: 1.5rem;
            color: var(--text-heading);
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}
        
        #sidebar nav ul {{
            list-style: none;
        }}
        
        #sidebar nav li {{
            margin-bottom: 0.5rem;
        }}
        
        #sidebar nav a {{
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--text-primary);
            text-decoration: none;
            border-radius: 4px;
            transition: all 0.2s ease;
            font-size: 0.95rem;
        }}
        
        #sidebar nav a:hover {{
            background-color: var(--bg-nav-hover);
            color: var(--text-heading);
            transform: translateX(4px);
        }}
        
        #sidebar nav a.active {{
            background-color: var(--bg-nav-hover);
            color: var(--text-link);
            font-weight: 500;
        }}
        
        /* 主内容区域 */
        #content {{
            margin-left: 280px;
            padding: 3rem 4rem;
            max-width: 900px;
            flex: 1;
        }}
        
        /* 章节样式 */
        .section {{
            margin-bottom: 4rem;
            padding-top: 1rem;
        }}
        
        .section:target {{
            padding-top: 2rem;
            margin-top: -2rem;
        }}
        
        /* 标题样式 */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-heading);
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            line-height: 1.4;
        }}
        
        h1 {{
            font-size: 2.5rem;
            border-bottom: 3px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 2rem;
        }}
        
        h2 {{
            font-size: 2rem;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.4rem;
        }}
        
        h3 {{
            font-size: 1.5rem;
        }}
        
        h4 {{
            font-size: 1.25rem;
        }}
        
        /* 段落和文本 */
        p {{
            margin-bottom: 1.2rem;
            text-align: justify;
        }}
        
        /* 链接 */
        a {{
            color: var(--text-link);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.2s ease;
        }}
        
        a:hover {{
            color: var(--text-link-hover);
            border-bottom-color: var(--text-link-hover);
        }}
        
        /* 列表 */
        ul, ol {{
            margin-bottom: 1.2rem;
            padding-left: 2rem;
        }}
        
        li {{
            margin-bottom: 0.5rem;
        }}
        
        /* 代码块 */
        code {{
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.9em;
            color: var(--text-heading);
        }}
        
        pre {{
            background-color: var(--code-bg);
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 1.2rem;
            border: 1px solid var(--border-color);
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        /* 引用 */
        blockquote {{
            border-left: 4px solid var(--text-link);
            padding-left: 1.5rem;
            margin: 1.5rem 0;
            color: var(--text-primary);
            font-style: italic;
        }}
        
        /* 表格 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
        }}
        
        th, td {{
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            text-align: left;
        }}
        
        th {{
            background-color: var(--code-bg);
            color: var(--text-heading);
            font-weight: 600;
        }}
        
        /* 分隔线 */
        hr {{
            border: none;
            border-top: 2px solid var(--border-color);
            margin: 2rem 0;
        }}
        
        /* 滚动条美化 */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-sidebar);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-primary);
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            #sidebar {{
                width: 100%;
                position: relative;
                height: auto;
                border-right: none;
                border-bottom: 1px solid var(--border-color);
            }}
            
            #content {{
                margin-left: 0;
                padding: 2rem 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <aside id="sidebar">
        <h1>{title}</h1>
        <nav>
            <ul>
{nav_items}
            </ul>
        </nav>
    </aside>
    
    <main id="content">
{content}
    </main>
    
    <script>
        // 导航高亮显示
        document.addEventListener('DOMContentLoaded', function() {{
            const links = document.querySelectorAll('#sidebar nav a');
            const sections = document.querySelectorAll('.section');
            
            function setActiveLink() {{
                let index = sections.length;
                
                while(--index && window.scrollY + 100 < sections[index].offsetTop) {{}}
                
                links.forEach((link) => link.classList.remove('active'));
                if (links[index]) {{
                    links[index].classList.add('active');
                }}
            }}
            
            setActiveLink();
            window.addEventListener('scroll', setActiveLink);
        }});
    </script>
</body>
</html>
"""


def get_markdown_files(directory: Path) -> List[Path]:
    """
    Get all markdown files in a directory, sorted by name.
    
    Args:
        directory: Directory to search for markdown files
        
    Returns:
        List of markdown file paths, sorted
    """
    md_files = list(directory.glob("*.md"))
    md_files.extend(directory.glob("*.markdown"))
    return sorted(md_files)


def convert_markdown_to_html(md_content: str) -> str:
    """
    Convert markdown content to HTML.
    
    Args:
        md_content: Markdown content string
        
    Returns:
        HTML string
    """
    md = markdown.Markdown(extensions=[
        'extra',          # Tables, fenced code blocks, etc.
        'codehilite',     # Syntax highlighting
        'toc',            # Table of contents
        'nl2br',          # New line to break
    ])
    return md.convert(md_content)


def merge_markdown_files(
    input_dir: Path,
    output_file: Path = None,
    title: str = None,
) -> None:
    """
    Merge multiple markdown files into a single HTML page.
    
    Args:
        input_dir: Directory containing markdown files
        output_file: Output HTML file path (default: merged.html in input directory)
        title: Page title (default: directory name)
        
    Raises:
        FileNotFoundError: If input directory doesn't exist
        ValueError: If no markdown files found
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    if not input_dir.is_dir():
        raise ValueError(f"Path is not a directory: {input_dir}")
    
    # Get all markdown files
    md_files = get_markdown_files(input_dir)
    
    if not md_files:
        raise ValueError(f"No markdown files found in: {input_dir}")
    
    # Determine title and output file
    if title is None:
        title = input_dir.name
    
    if output_file is None:
        output_file = input_dir / "merged.html"
    
    print(f"Found {len(md_files)} markdown files in: {input_dir}")
    print(f"Merging into: {output_file}")
    
    # Build navigation and content
    nav_items = []
    content_sections = []
    
    for idx, md_file in enumerate(md_files, 1):
        print(f"  Processing: {md_file.name}")
        
        # Read markdown content
        md_content = md_file.read_text(encoding='utf-8')
        
        # Convert to HTML
        html_content = convert_markdown_to_html(md_content)
        
        # Create section ID from filename
        section_id = f"section-{idx}"
        section_title = md_file.stem
        
        # Remove numbering prefix if exists (e.g., "01_" -> "")
        if section_title and len(section_title) > 3 and section_title[2] == '_':
            section_title = section_title[3:]
        
        # Add to navigation
        nav_items.append(f'                <li><a href="#{section_id}">{section_title}</a></li>')
        
        # Add to content
        content_sections.append(f'        <section id="{section_id}" class="section">\n{html_content}\n        </section>')
    
    # Generate final HTML
    html = HTML_TEMPLATE.format(
        title=title,
        nav_items='\n'.join(nav_items),
        content='\n\n'.join(content_sections),
    )
    
    # Write output file
    output_file.write_text(html, encoding='utf-8')
    
    print(f"\n✓ Successfully merged {len(md_files)} files into HTML")
    print(f"✓ Output: {output_file}")


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Merge Markdown files into a single HTML page with navigation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing markdown files to merge",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output HTML file path (default: merged.html in input directory)",
    )
    
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        help="Page title (default: directory name)",
    )
    
    args = parser.parse_args()
    
    try:
        merge_markdown_files(
            input_dir=args.input_dir,
            output_file=args.output,
            title=args.title,
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
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
