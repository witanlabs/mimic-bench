#!/usr/bin/env python3
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from shared_oracle_runtime import ChartOracle, protocol_error, query_budget


BUDGET = query_budget()
LOG = Path(os.getenv("QUERY_LOG", "/var/log/oracle/queries.jsonl"))
count = 0
lock = threading.Lock()
oracle = None


def ask(case):
    global oracle
    if oracle is None:
        oracle = ChartOracle()
    return oracle.render_case(case)


def handle(line):
    global count
    with lock:
        if count >= BUDGET:
            return protocol_error("query_budget_exceeded", budget=BUDGET)
        count += 1
        index = count
    try:
        response = ask(json.loads(line))
    except json.JSONDecodeError:
        response = protocol_error("malformed_json")
    except Exception as exc:
        response = protocol_error("oracle_backend_error", detail=str(exc))
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({"query_index": index, "request": line, "response": response}) + "\n")
    except OSError:
        pass
    return response


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.path == "/health" else 404)
        self.end_headers()
        if self.path == "/health":
            self.wfile.write(b"ok\n")

    def do_POST(self):
        if self.path != "/query":
            self.send_response(404)
            self.end_headers()
            return
        body = self.rfile.read(int(self.headers.get("content-length", "0"))).decode()
        out = "\n".join(json.dumps(handle(line), sort_keys=True) for line in body.splitlines() if line.strip())
        out = (out + "\n").encode() if out else b""
        self.send_response(200)
        self.send_header("Content-Type", "application/jsonl")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *_):
        pass


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

