import html
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

import psycopg


def connect():
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with connect() as conn:
            rows = conn.execute("SELECT id, body FROM notes ORDER BY id").fetchall()
        items = "".join(f"<li>{html.escape(body)}</li>" for _, body in rows)
        page = f"""<!doctype html>
<html><body>
<h1>Notes</h1>
<form method="post">
<input name="body" autofocus>
<button>Save</button>
</form>
<ul>{items}</ul>
</body></html>"""
        data = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode())
        text = form.get("body", [""])[0].strip()
        if text:
            with connect() as conn:
                conn.execute("INSERT INTO notes (body) VALUES (%s)", (text,))
                conn.commit()
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()