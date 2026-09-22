"""Static server for the project that also accepts rendered PNGs from tools/render.html.

    python tools/serve.py            # http://localhost:8766/tools/render.html

POST /save?name=<file>.png writes the body to assets/<file>.png.
"""
import http.server
import os
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def do_POST(self):
        q = urllib.parse.urlparse(self.path)
        name = os.path.basename(urllib.parse.parse_qs(q.query).get("name", [""])[0])
        if q.path != "/save" or not name.endswith(".png"):
            self.send_error(400)
            return
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        os.makedirs(ASSETS, exist_ok=True)
        with open(os.path.join(ASSETS, name), "wb") as f:
            f.write(data)
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
