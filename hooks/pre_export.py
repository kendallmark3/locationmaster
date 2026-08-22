def validate_exportable_project(project: dict) -> list[str]:
    errors: list[str] = []
    if not project.get("intent"):
        errors.append("Project intent is required.")
    points = project.get("points") or []
    if not points:
        errors.append("At least one story point is required.")
    for point in points:
        if point.get("visible", True):
            if point.get("latitude") is None or point.get("longitude") is None:
                errors.append(f"Visible point {point.get('id')} has no coordinates.")
            if not point.get("label"):
                errors.append(f"Visible point {point.get('id')} has no label.")
            if not point.get("symbol"):
                errors.append(f"Visible point {point.get('id')} has no symbol.")
    return errors
