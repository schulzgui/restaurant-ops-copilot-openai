"""Authenticated local HTTP app. Separate operator and reviewer capabilities."""
import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .domain import DomainError
from .engine import Engine

STATIC = Path(__file__).parent / "static"

def make_server(store, provider, port=8004, operator_token=None, reviewer_token=None, host="127.0.0.1"):
    operator_token = operator_token or secrets.token_urlsafe(24)
    reviewer_token = reviewer_token or secrets.token_urlsafe(24)
    if operator_token == reviewer_token or min(len(operator_token), len(reviewer_token)) < 20:
        raise ValueError("Tokens distintos com pelo menos 20 caracteres são obrigatórios")
    slots = threading.BoundedSemaphore(2)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, body, content_type="application/json"):
            data = json.dumps(body, ensure_ascii=False).encode() if content_type == "application/json" else body
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers(); self.wfile.write(data)

        def role(self):
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            if hmac.compare_digest(token.encode(), reviewer_token.encode()):
                return "reviewer"
            if hmac.compare_digest(token.encode(), operator_token.encode()):
                return "operator"
            return None

        def valid_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_GET(self):
            if not self.valid_host():
                return self.respond(403, {"error": "Host não permitido"})
            path = urlparse(self.path).path
            if path == "/health":
                return self.respond(200, {"status": "ok", "mode": getattr(provider, "mode", "live"), "synthetic_data": True})
            assets = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
            if path in assets:
                name, kind = assets[path]
                return self.respond(200, (STATIC / name).read_bytes(), kind)
            if not self.role():
                return self.respond(401, {"error": "Token inválido"})
            if path == "/api/dashboard":
                return self.respond(200, {**store.dashboard(), "role": self.role(), "mode": getattr(provider, "mode", "live")})
            if path == "/api/audit":
                return self.respond(200, store.audit())
            return self.respond(404, {"error": "Rota inexistente"})

        def do_POST(self):
            if not self.valid_host():
                return self.respond(403, {"error": "Host não permitido"})
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                return self.respond(403, {"error": "Origem não permitida"})
            role = self.role()
            if role is None:
                return self.respond(401, {"error": "Token inválido"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.respond(415, {"error": "Use JSON"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    return self.respond(413, {"error": "Corpo vazio ou maior que 16 KiB"})
                self.connection.settimeout(10)
                obj = json.loads(self.rfile.read(length))
                if not isinstance(obj, dict):
                    raise DomainError("Objeto JSON obrigatório")
                path = urlparse(self.path).path
                if path == "/api/run":
                    if role != "operator":
                        return self.respond(403, {"error": "Use token de operador"})
                    if not slots.acquire(blocking=False):
                        return self.respond(429, {"error": "Duas execuções já estão em andamento"})
                    try:
                        result = Engine(store, provider).run(obj.get("prompt"))
                    finally:
                        slots.release()
                    return self.respond(200, result)
                if path in {"/api/review", "/api/dispatch", "/api/requeue"}:
                    if role != "reviewer":
                        return self.respond(403, {"error": "Revisor obrigatório"})
                    if path == "/api/review":
                        result = store.review(obj["proposal_id"], obj["decision"], "reviewer-local", obj["version"])
                    elif path == "/api/requeue":
                        store.requeue(obj["proposal_id"], "reviewer-local"); result = {"requeued": True}
                    else:
                        result = {"receipts": store.dispatch(), "external_message_sent": False}
                    return self.respond(200, result)
                return self.respond(404, {"error": "Rota inexistente"})
            except (DomainError, ValueError, KeyError, TypeError):
                return self.respond(400, {"error": "Entrada inválida, estado desatualizado ou transição não permitida"})
            except TimeoutError:
                return self.respond(408, {"error": "Tempo de leitura excedido"})

    server = ThreadingHTTPServer((host, port), Handler)
    return server, operator_token, reviewer_token
