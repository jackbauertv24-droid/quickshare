#!/usr/bin/env python3
import http.server
import socketserver
import os
import re
from datetime import datetime
import html as html_module

PORT = int(os.environ.get('PORT', 8000))
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', './uploads')
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))


def sanitize_filename(filename):
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\.\-]', '_', filename)
    return filename[:100] if filename else 'unnamed'


def get_upload_files():
    if not os.path.exists(UPLOAD_DIR):
        return []
    files = []
    for f in sorted(os.listdir(UPLOAD_DIR), reverse=True):
        path = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(path):
            files.append({'name': f, 'size': os.path.getsize(path)})
    return files


class UploadHandler(http.server.BaseHTTPRequestHandler):
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

            files = get_upload_files()
            files_html = ''
            if files:
                files_html = '<h2>Uploaded Files</h2><ul>'
                for f in files:
                    size_kb = f['size'] / 1000
                    files_html += f'<li>{html_module.escape(f["name"])} ({size_kb:.1f} KB)</li>'
                files_html += '</ul>'
            else:
                files_html = '<p><em>No files uploaded yet.</em></p>'

            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>QuickShare Upload</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
                    form {{ border: 1px solid #ccc; padding: 2rem; border-radius: 5px; background: #f9f9f9; }}
                    input[type="file"] {{ margin: 1rem 0; }}
                    input[type="submit"] {{ background: #28a745; color: white; border: none; padding: 0.5rem 1rem; border-radius: 3px; cursor: pointer; font-size: 1rem; }}
                    input[type="submit"]:hover {{ background: #218838; }}
                    .info {{ background: #e7f3ff; padding: 1rem; border-radius: 5px; margin-bottom: 1rem; }}
                    ul {{ list-style: none; padding: 0; }}
                    li {{ padding: 0.5rem; border-bottom: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <h1>QuickShare Upload</h1>
                <div class="info">
                    <strong>Max file size:</strong> {MAX_FILE_SIZE // (1024*1024)} MB<br>
                    <strong>Duration:</strong> Server runs for a limited time only
                </div>
                <form method="post" enctype="multipart/form-data">
                    <p>Select a file to upload:</p>
                    <input type="file" name="file" required>
                    <br>
                    <input type="submit" value="Upload File">
                </form>
                {files_html}
            </body>
            </html>
            '''
            self.wfile.write(html_content.encode('utf-8'))
            return

        self.send_error(404, 'Not Found')

    def do_POST(self):
        if self.path != '/':
            self.send_error(404, 'Not Found')
            return

        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, 'Bad Request')
            return

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > MAX_FILE_SIZE + 4096:
            self.send_error(413, 'File too large')
            return

        body = self.rfile.read(content_length)

        boundary = content_type.split('boundary=')[1].encode()
        parts = body.split(b'--' + boundary)

        file_data = None
        original_filename = 'unnamed'

        for part in parts:
            if b'Content-Disposition' in part and b'name="file"' in part:
                headers_content = part.split(b'\r\n\r\n', 1)
                if len(headers_content) != 2:
                    continue

                header = headers_content[0].decode('utf-8', errors='ignore')
                match = re.search(r'filename="([^"]+)"', header)
                if match:
                    original_filename = match.group(1)

                file_data = headers_content[1].rstrip(b'\r\n')
                break

        if file_data is None:
            self.send_error(400, 'No file uploaded')
            return

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        safe_name = sanitize_filename(original_filename)
        filename = f'{timestamp}_{safe_name}'
        filepath = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(filepath, 'wb') as f:
                f.write(file_data)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            response = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Upload Complete</title>
                <meta charset="utf-8">
                <style>body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}</style>
            </head>
            <body>
                <h1>Upload Successful!</h1>
                <p>File saved as: {html_module.escape(filename)}</p>
                <p>Size: {len(file_data) / 1000:.1f} KB</p>
                <p><a href="/">Upload another file</a></p>
            </body>
            </html>
            '''
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f'Error saving file: {html_module.escape(str(e))}')


def main():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), UploadHandler) as httpd:
        print(f"QuickShare server running on port {PORT}")
        print(f"Upload directory: {os.path.abspath(UPLOAD_DIR)}")
        print(f"Max file size: {MAX_FILE_SIZE // (1024*1024)} MB")
        httpd.serve_forever()


if __name__ == "__main__":
    main()