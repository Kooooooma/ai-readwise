#!/usr/bin/env python3
"""
Simple HTTP Server

A lightweight HTTP server for serving static files.
Uses Python's built-in http.server module - no external dependencies required.
"""

import argparse
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path


class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with detailed logging."""
    
    def do_POST(self):
        """Handle POST requests and log the body."""
        # Read the POST body
        content_length = self.headers.get('Content-Length')
        post_body = None
        
        if content_length:
            try:
                content_length = int(content_length)
                post_body = self.rfile.read(content_length)
                # Store it for logging
                self.post_body = post_body
            except Exception as e:
                print(f"⚠️  Error reading POST body: {e}")
                self.post_body = None
        
        # Call parent's POST handler
        return super().do_POST()
    
    def log_message(self, format, *args):
        """Override to provide detailed log messages."""
        from urllib.parse import urlparse, parse_qs
        
        # Get client address
        client = self.client_address[0]
        
        # Parse URL and query parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Show detailed request info
        print(f"\n{'='*60}")
        print(f"📨 Request from: {client}")
        print(f"🔗 Method: {self.command}")
        print(f"📄 Path: {path}")
        print(f"📊 Status: {args[1]}")
        
        # Show query parameters if present
        if query_params:
            print(f"\n🔍 Query Parameters:")
            for key, values in query_params.items():
                for value in values:
                    print(f"  {key} = {value}")
        
        # Show POST body if present
        if hasattr(self, 'post_body') and self.post_body:
            print(f"\n📦 POST Body ({len(self.post_body)} bytes):")
            try:
                # Try to decode as UTF-8
                body_text = self.post_body.decode('utf-8')
                # Limit output length
                if len(body_text) > 500:
                    print(f"  {body_text[:500]}...")
                    print(f"  [... truncated, total {len(body_text)} characters]")
                else:
                    print(f"  {body_text}")
            except UnicodeDecodeError:
                # If not text, show hex preview
                hex_preview = self.post_body[:50].hex()
                print(f"  [Binary data] {hex_preview}...")
        
        # Show important headers
        if hasattr(self, 'headers'):
            print(f"\n📋 Headers:")
            for header in ['User-Agent', 'Referer', 'Accept', 'Host', 'Content-Type', 'Content-Length']:
                if header in self.headers:
                    value = self.headers[header]
                    # Truncate long values
                    if len(value) > 80:
                        value = value[:77] + "..."
                    print(f"  {header}: {value}")
        
        print(f"{'='*60}\n")


def find_html_file(directory: Path) -> Path:
    """
    Find the first HTML file in the directory.
    Prioritizes 'merged.html' if it exists.
    
    Args:
        directory: Directory to search
        
    Returns:
        Path to HTML file, or None if not found
    """
    # First, try to find merged.html
    merged = directory / "merged.html"
    if merged.exists():
        return merged
    
    # Otherwise, find any HTML file
    html_files = list(directory.glob("*.html"))
    if html_files:
        return html_files[0]
    
    return None


def serve_directory(
    directory: Path,
    port: int = 8000,
    open_browser: bool = True,
) -> None:
    """
    Start an HTTP server to serve files from a directory.
    
    Args:
        directory: Directory to serve
        port: Port number (default: 8000)
        open_browser: Whether to automatically open browser (default: True)
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        OSError: If port is already in use
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    # Change to the directory to serve
    os.chdir(directory)
    
    # Create server
    Handler = QuietHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            server_url = f"http://localhost:{port}"
            
            print("\n" + "="*60)
            print(f"🚀 HTTP Server started!")
            print(f"📁 Serving directory: {directory.absolute()}")
            print(f"🌐 Server URL: {server_url}")
            print("="*60)
            
            # Try to find and suggest HTML file
            html_file = find_html_file(directory)
            if html_file:
                file_url = f"{server_url}/{html_file.name}"
                print(f"\n✨ Found HTML file: {html_file.name}")
                print(f"🔗 Direct link: {file_url}")
                
                # Open browser if requested
                if open_browser:
                    print(f"\n🌐 Opening in browser...")
                    webbrowser.open(file_url)
            else:
                print(f"\n📋 Browse files at: {server_url}")
                if open_browser:
                    webbrowser.open(server_url)
            
            print(f"\n💡 Press Ctrl+C to stop the server")
            print("="*60 + "\n")
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            raise OSError(
                f"Port {port} is already in use. "
                f"Try a different port with -p option."
            ) from e
        raise
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("🛑 Server stopped by user")
        print("="*60)


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Start a simple HTTP server to serve HTML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Serve current directory on default port 8000
  python serve_html.py .
  
  # Serve specific directory
  python serve_html.py shoedog/shoedog
  
  # Use custom port
  python serve_html.py shoedog/shoedog -p 8080
  
  # Don't auto-open browser
  python serve_html.py . --no-browser
        """,
    )
    
    parser.add_argument(
        "directory",
        type=Path,
        nargs='?',
        default=Path.cwd(),
        help="Directory to serve (default: current directory)",
    )
    
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port number (default: 8000)",
    )
    
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser",
    )
    
    args = parser.parse_args()
    
    try:
        serve_directory(
            directory=args.directory,
            port=args.port,
            open_browser=not args.no_browser,
        )
        return 0
    
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        return 0
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
