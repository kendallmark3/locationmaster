from io import BytesIO
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .models import Project, StoryPoint


def render_project_image(
    project: Project,
    image_format: str,
    width: int,
    height: int,
) -> bytes:
    canvas = Image.new("RGB", (width, height), color="#f6f7fb")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    padding = 24
    header_h = 88
    map_left = padding
    map_top = padding + header_h
    map_right = width - padding
    map_bottom = height - padding
    map_w = max(1, map_right - map_left)
    map_h = max(1, map_bottom - map_top)

    draw.text((padding, padding), project.name, fill="#111827", font=font)
    intent = project.rawIntent.strip() or "Untitled intent"
    draw.text((padding, padding + 22), _truncate(intent, 120), fill="#374151", font=font)

    draw.rectangle((map_left, map_top, map_right, map_bottom), fill="#e5e7eb", outline="#cbd5e1", width=2)

    visible_points = [point for point in project.points if point.visible]
    if visible_points:
        min_lon, max_lon, min_lat, max_lat = _bounds(visible_points)
        lon_span = max(max_lon - min_lon, 0.001)
        lat_span = max(max_lat - min_lat, 0.001)

        for point in visible_points:
            x = map_left + ((point.longitude - min_lon) / lon_span) * map_w
            y = map_bottom - ((point.latitude - min_lat) / lat_span) * map_h
            radius = max(4, int(4 * point.size))
            color = "#dc2626" if point.symbol == "subject" else "#2563eb"
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline="#ffffff", width=2)
            draw.text((x + radius + 3, y - radius - 1), _truncate(point.label, 28), fill="#111827", font=font)
    else:
        draw.text((map_left + 12, map_top + 12), "No visible points", fill="#6b7280", font=font)

    output = BytesIO()
    pil_format = "PNG" if image_format == "png" else "JPEG"
    canvas.save(output, format=pil_format, quality=90)
    return output.getvalue()


def _bounds(points: Iterable[StoryPoint]) -> tuple[float, float, float, float]:
    longitudes = [point.longitude for point in points]
    latitudes = [point.latitude for point in points]
    return min(longitudes), max(longitudes), min(latitudes), max(latitudes)


def _truncate(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return value[: length - 1].rstrip() + "…"
