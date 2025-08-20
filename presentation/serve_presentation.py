#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def serve_presentation(presentation_file):
    """Serve a presentation file via HTTP server"""
    if not Path(presentation_file).exists():
        print(f"Error: {presentation_file} not found")
        sys.exit(1)
    
    # Try different ports
    ports = [8000, 8001, 8002, 8003, 8080]
    
    for port in ports:
        try:
            with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                print(f"🚀 Serving presentation at http://localhost:{port}/{presentation_file}")
                print(f"📱 Mobile access: http://[your-ip]:{port}/{presentation_file}")
                print("\n🎮 Presentation Controls:")
                print("  - Arrow keys: Navigate slides")
                print("  - F: Fullscreen mode")
                print("  - S: Speaker notes")
                print("  - O: Overview mode")
                print("  - ?: Help")
                print("\n⏹️  Press Ctrl+C to stop the server")
                
                # Open in browser
                webbrowser.open(f"http://localhost:{port}/{presentation_file}")
                
                # Start serving
                httpd.serve_forever()
                
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} is busy, trying next port...")
                continue
            else:
                print(f"Error starting server on port {port}: {e}")
                continue
    
    print("❌ Could not start server on any available port")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python serve_presentation.py <presentation_file>")
        sys.exit(1)
    
    presentation_file = sys.argv[1]
    serve_presentation(presentation_file)