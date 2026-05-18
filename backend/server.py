import json
import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
QUOTES_FILE = os.environ.get("QUOTES_FILE", os.path.join(HERE, "quotes.json"))
os.makedirs(os.path.dirname(os.path.abspath(QUOTES_FILE)) or ".", exist_ok=True)

DEFAULT_QUOTES = [
    {"quote": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
    {"quote": "In the middle of every difficulty lies opportunity.", "author": "Albert Einstein"},
    {"quote": "Whether you think you can, or you think you can't — you're right.", "author": "Henry Ford"},
    {"quote": "Simplicity is the ultimate sophistication.", "author": "Leonardo da Vinci"},
    {"quote": "Talk is cheap. Show me the code.", "author": "Linus Torvalds"},
    {"quote": "Premature optimization is the root of all evil.", "author": "Donald Knuth"},
    {"quote": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
    {"quote": "Stay hungry, stay foolish.", "author": "Stewart Brand"},
    {"quote": "Make it work, make it right, make it fast.", "author": "Kent Beck"},
    {"quote": "Programs must be written for people to read, and only incidentally for machines to execute.", "author": "Harold Abelson"},
]

_lock = threading.Lock()


def _load_quotes():
    """Load quotes from disk, seeding the file with defaults if it doesn't exist."""
    if not os.path.exists(QUOTES_FILE):
        with open(QUOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_QUOTES, f, indent=2, ensure_ascii=False)
        return list(DEFAULT_QUOTES)
    try:
        with open(QUOTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return list(DEFAULT_QUOTES)


def _save_quotes(quotes):
    """Persist quotes to disk atomically-ish via write-then-rename."""
    tmp = QUOTES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    os.replace(tmp, QUOTES_FILE)


QUOTES = _load_quotes()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
            return

        if self.path == "/api/quote":
            with _lock:
                quote = random.choice(QUOTES) if QUOTES else None
            if quote is None:
                self._send_json(404, {"error": "no quotes available"})
                return
            self._send_json(200, quote)
            return

        if self.path == "/api/quotes":
            with _lock:
                self._send_json(200, list(QUOTES))
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path != "/api/quote":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            self._send_json(400, {"error": "empty body"})
            return

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid JSON"})
            return

        quote_text = (data.get("quote") or "").strip() if isinstance(data, dict) else ""
        author     = (data.get("author") or "Anonymous").strip() if isinstance(data, dict) else ""
        if not quote_text:
            self._send_json(400, {"error": "missing 'quote' field"})
            return

        new_quote = {"quote": quote_text, "author": author or "Anonymous"}
        with _lock:
            QUOTES.append(new_quote)
            _save_quotes(QUOTES)
            total = len(QUOTES)

        self._send_json(201, {"ok": True, "added": new_quote, "total": total})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        print("[server] " + fmt % args)


def main():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Quote server running at http://localhost:{port}/")
    print(f"Using quotes file: {QUOTES_FILE}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
