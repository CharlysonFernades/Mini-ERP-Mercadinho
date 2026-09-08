"""Servidor local da interface. Python 3.10+, sem instalação de pacotes."""

import argparse
import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from erp_web import ERPError, ERPStore

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "frontend"


class ERPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store):
        self.store = store
        self.csrf = secrets.token_urlsafe(32)
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def response(self, status, body, mime="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(raw)

    def allowed_host(self):
        # Limita DNS rebinding; terminal.local é usado apenas pela prévia supervisionada.
        host = urlsplit("http://" + self.headers.get("Host", "")).hostname
        return host in {"localhost", "127.0.0.1", "::1", "terminal.local"}

    def do_GET(self):
        if not self.allowed_host():
            return self.response(403, {"error": "Host não autorizado."})
        path = urlsplit(self.path).path
        if path == "/api/state":
            try:
                return self.response(200, {**self.server.store.snapshot(), "csrf": self.server.csrf})
            except (ERPError, OSError) as error:
                return self.response(getattr(error, "status", 500), {"error": str(error) if isinstance(error, ERPError) else "Não foi possível acessar os dados."})
        files = {
            "/": "index.html",
            "/index.html": "index.html",
            "/app.js": "app.js",
            "/styles.css": "styles.css",
            "/enhancements.css": "enhancements.css",
            "/favicon.svg": "favicon.svg",
        }
        if path not in files:
            return self.response(404, {"error": "Página não encontrada."})
        file = STATIC / files[path]
        self.response(200, file.read_bytes(), (mimetypes.guess_type(file.name)[0] or "application/octet-stream") + "; charset=utf-8")

    def do_POST(self):
        if not self.allowed_host() or self.headers.get("Sec-Fetch-Site") == "cross-site":
            return self.response(403, {"error": "Origem não autorizada."})
        if not secrets.compare_digest(self.headers.get("X-ERP-Token", ""), self.server.csrf):
            return self.response(403, {"error": "Sessão desatualizada. Recarregue a página."})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.response(415, {"error": "Formato de dados inválido."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16_384:
                raise ERPError("Tamanho da solicitação inválido.")
            body = json.loads(self.rfile.read(length))
            routes = {"/api/products": "create", "/api/products/update": "update", "/api/products/delete": "delete", "/api/movements": "movement"}
            action = routes.get(urlsplit(self.path).path)
            if not action:
                raise ERPError("Operação não encontrada.", 404)
            result = self.server.store.mutate(action, body)
            self.response(201 if action == "create" else 200, {**result, "csrf": self.server.csrf})
        except ERPError as error:
            self.response(error.status, {"error": str(error)})
        except (ValueError, UnicodeError):
            self.response(400, {"error": "Dados inválidos. Confira os campos."})
        except OSError:
            self.response(500, {"error": "Não foi possível salvar. Recarregue a página para conferir a operação antes de tentar novamente."})


def main():
    parser = argparse.ArgumentParser(description="Mini ERP Mercadinho — interface local")
    parser.add_argument("--demo", action="store_true", help="Dados de exemplo separados em .erp-demo")
    parser.add_argument("--data-dir", type=Path, help="Pasta alternativa dos arquivos JSON")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    # A prévia encaminha essa opção; HTTPServer já falha se a porta estiver ocupada.
    parser.add_argument("--strictPort", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    directory = args.data_dir or (ROOT / ".erp-demo" if args.demo else ROOT)
    store = ERPStore(directory, demo=args.demo)
    server = ERPServer((args.host, args.port), store)
    print(f"Mini ERP em http://localhost:{args.port} — {'demonstração' if args.demo else 'dados do projeto'}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
