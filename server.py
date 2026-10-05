"""Serve all flow editors and local video exports on one port."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'flow-library'))
import ribbon_server, light_stream_server, dot_server, chart_server
from portrait_export import portrait_get, portrait_post

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if not portrait_get(self):
            super().do_GET()

    def do_POST(self):
        if portrait_post(self):
            return
        if self.path == '/export-dots':
            dot_server.Handler.do_POST(self)
        elif self.path == '/export-chart':
            chart_server.Handler.do_POST(self)
        elif self.path == '/export':
            if '/light-stream-animation.html' in self.headers.get('Referer', ''):
                light_stream_server.Handler.do_POST(self)
            else:
                ribbon_server.Handler.do_POST(self)
        else:
            self.send_error(404)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8048)
    args = parser.parse_args()
    (ROOT / 'work').mkdir(exist_ok=True)
    print(f'Open http://127.0.0.1:{args.port}/flow-library/index.html', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
