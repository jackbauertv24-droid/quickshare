#!/usr/bin/env python3
import http.server
import socketserver
from urllib.parse import parse_qs
import html
import os

PORT = 8000
UPLOAD_FILE = "./uploaded_file.bin"  # Only this single file can be written

class SimpleUploadHandler(http.server.SimpleHTTPRequestHandler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_request(self, code='-', size='-'):
        if self.path == '/favicon.ico':
            return
        super().log_request(code, size)

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Simple File Upload</title>
                <meta charset=\"utf-8\">
                <style>
                    body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
                    form {{ border: 1px solid #ccc; padding: 2rem; border-radius: 5px; }}
                    input[type=\"file\"] {{ margin: 1rem 0; }}
                    input[type=\"submit\"] {{ background: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 3px; cursor: pointer; }}
                </style>
            </head>
            <body>
                <h1>File Upload</h1>
                <form method=\"post\" enctype=\"multipart/form-data\">
                    <p>Select a file to upload:</p>
                    <input type=\"file\" name=\"uploaded_file\" required>
                    <br>
                    <input type=\"submit\" value=\"Upload File\">
                </form>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_error(404, 'Not Found')
    
    def do_POST(self):
        if self.path != '/':
            self.send_error(404, 'Not Found')
            return
            
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, 'Bad Request')
            return
            
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Parse multipart form data manually to avoid dependencies
        boundary = content_type.split('boundary=')[1].encode()
        parts = body.split(b'--' + boundary)
        
        uploaded_file_data = None
        for part in parts:
            if b'Content-Disposition' in part and b'name=\"uploaded_file\"' in part:
                # Split headers and content
                headers_content = part.split(b'\r\n\r\n', 1)
                if len(headers_content) != 2:
                    continue
                uploaded_file_data = headers_content[1].rstrip(b'\r\n')
                break
        
        if uploaded_file_data is None:
            self.send_error(400, 'No file uploaded')
            return
            
        try:
            # Security: Only write to the specific pre-defined file
            # No path traversal possible, only overwriting this single file
            with open(UPLOAD_FILE, 'wb') as f:
                f.write(uploaded_file_data)
            
            file_size_kb = len(uploaded_file_data) / 1000
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Upload Complete</title>
                <meta charset=\"utf-8\">
                <style>body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}</style>
            </head>
            <body>
                <h1>Upload Successful!</h1>
                <p>File was uploaded successfully. Size: {file_size_kb:.1f} KB</p>
                <p><a href=\"/\">Upload another file</a></p>
            </body>
            </html>
            """
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f'Error writing file: {html.escape(str(e))}')

def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), SimpleUploadHandler) as httpd:
        print(f"Serving on port {PORT}")
        print(f"⚠️  WARNING: This server allows anyone to overwrite {UPLOAD_FILE}")
        print(f"Only the predefined file can be written - no arbitrary file writes are possible")
        print(f"No filesystem browsing is allowed")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
