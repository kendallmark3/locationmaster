from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[1]
contracts = ROOT / "contracts"
errors = []

for path in contracts.glob("*.schema.json"):
    try:
        data = json.loads(path.read_text())
        if data.get("type") != "object":
            errors.append(f"{path.name}: top-level type must be object")
        if "required" not in data:
            errors.append(f"{path.name}: required fields missing")
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print(f"Validated {len(list(contracts.glob('*.schema.json')))} contracts.")
