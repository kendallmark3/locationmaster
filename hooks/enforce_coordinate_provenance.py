import json, sys
from pathlib import Path

def validate(project):
    errors = []
    for point in project.get("points", []):
        if point.get("longitude") is None or point.get("latitude") is None:
            errors.append(f"{point.get('id')}: missing coordinates")
        if point.get("coordinateSource") not in {"geocoder","map_click","import"}:
            errors.append(f"{point.get('id')}: invalid coordinateSource")
        if point.get("coordinateSource") == "geocoder" and not point.get("providerPlaceId"):
            errors.append(f"{point.get('id')}: geocoded point missing providerPlaceId")
    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: enforce_coordinate_provenance.py project.json")
        raise SystemExit(0)
    project = json.loads(Path(sys.argv[1]).read_text())
    errors = validate(project)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print("Coordinate provenance valid.")
