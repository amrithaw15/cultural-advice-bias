#!/usr/bin/env python3
"""
Simple HTTP server to serve the epistemic violence visualization
Run this script and then open http://localhost:8000/part1_fixed.html in your browser
"""

import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow fetch requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = MyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("=" * 80)
    print(f"Server started at http://localhost:{PORT}/")
    print(f"Open this URL in your browser:")
    print(f"    http://localhost:{PORT}/part1_fixed.html")
    print("=" * 80)
    print("Press Ctrl+C to stop the server")
    print()
    httpd.serve_forever()
