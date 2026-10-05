from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from portrait_export import portrait_get, portrait_post

ROOT = Path(__file__).resolve().parents[1]
ORIGINS = {f'http://127.0.0.1:{port}' for port in range(8043, 8048)}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        origin = self.headers.get('Origin')
        if origin in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        super().end_headers()

    def do_OPTIONS(self):
        if self.headers.get('Origin') not in ORIGINS:
            self.send_error(403)
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Frame-Rate')
        self.end_headers()

    def do_GET(self):
        if not portrait_get(self):
            super().do_GET()

    def do_POST(self):
        if self.headers.get('Origin') not in ORIGINS and self.headers.get('Origin') is not None:
            self.send_error(403)
            return
        if not portrait_post(self):
            self.send_error(404)

ThreadingHTTPServer(('127.0.0.1', 8047), Handler).serve_forever()
