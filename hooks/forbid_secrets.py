from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "node_modules", ".venv", "dist", "build"}
patterns = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
]
hits = []

for p in ROOT.rglob("*"):
    if not p.is_file() or any(part in SKIP for part in p.parts):
        continue
    if p.suffix.lower() in {".png",".jpg",".jpeg",".gif",".zip",".ico"}:
        continue
    try:
        text = p.read_text(errors="ignore")
    except Exception:
        continue
    for pat in patterns:
        if pat.search(text):
            hits.append(str(p.relative_to(ROOT)))
            break

if hits:
    print("Possible secrets found:\n" + "\n".join(hits))
    sys.exit(1)

print("No obvious committed secrets found.")
