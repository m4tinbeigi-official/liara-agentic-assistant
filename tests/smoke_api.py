import sys
import json
import requests

BASE = "http://localhost:3000"


def chat(msg: str):
    r = requests.post(f"{BASE}/api/v1/agent/chat", json={"message": msg}, timeout=60)
    tools = [l.strip() for l in r.text.splitlines() if '"tool"' in l]
    has_done = '"done"' in r.text
    print(f"MSG={msg[:40]!r} status={r.status_code} tools={tools} done={has_done}")
    return r


chat("Error: listen EADDRINUSE :::3000")
chat("وضعیت برنامه my-app را بگو")

r = chat("")
print("empty -> status:", r.status_code)

# search_docs path — check fallback answer content for port error
r = requests.post(
    f"{BASE}/api/v1/agent/chat",
    json={"message": "Error: listen EADDRINUSE :::3000"},
    timeout=120,
)
content = "".join(
    l[6:] for l in r.text.splitlines() if l.startswith("data: ") and '"content"' in l
)
texts = "".join(json.loads(l[6:])["text"] for l in r.text.splitlines() if l.startswith("data: ") and '"content"' in l)
print("--- assembled answer ---")
sys.stdout.buffer.write(texts[:600].encode("utf-8"))
print()
print("has EADDRINUSE explanation:", "EADDRINUSE" in texts or "PORT" in texts)
