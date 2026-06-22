#!/usr/bin/env python3
import json
import os
import sys
import urllib.request

try:
    req = urllib.request.Request(
        os.getenv("ORACLE_URL", "http://oracle-service:8000/query"),
        data=sys.stdin.buffer.read(),
        headers={"Content-Type": "application/jsonl"},
    )
    sys.stdout.buffer.write(urllib.request.urlopen(req, timeout=30).read())
except Exception as exc:
    print(json.dumps({"ok": False, "protocol_error": "oracle_unreachable", "detail": str(exc)}))

