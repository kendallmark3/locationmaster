from io import BytesIO
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .models import Project, StoryPoint

# Mirrors apps/web/src/main.tsx SYMBOL_COLORS so the exported image reads as the same
# visual story as the live map, not a separate red/blue placeholder.
SYMBOL_COLORS = {
    "subject": "#111111", "coffee": "#6f4e37", "restaurant": "#e2725b", "golf": "#2f855a",
    "school": "#2b6cb0", "park": "#2f855a", "transit": "#6b46c1", "hotel": "#b7791f",
    "grocery": "#2c7a7b", "company": "#4a5568", "employer": "#4a5568", "custom": "#718096",
}


def render_project_image(
    project: Project,
    image_format: str,
    width: int,
    height: int,
) -> bytes:
    canvas = Image.new("RGB", (width, height), color="#f6f7fb")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=22)
    subtitle_font = ImageFont.load_default(size=14)
    label_font = ImageFont.load_default(size=13)

    padding = 24
    header_h = 64
    map_left = padding
    map_top = padding + header_h
    map_right = width - padding
    map_bottom = height - padding
    map_w = max(1, map_right - map_left)
    map_h = max(1, map_bottom - map_top)
    label_margin = 6

    draw.text((padding, padding), project.name, fill="#111827", font=title_font)
    intent = project.rawIntent.strip() or "Untitled intent"
    draw.text((padding, padding + 28), _truncate(intent, 110), fill="#374151", font=subtitle_font)

    draw.rectangle((map_left, map_top, map_right, map_bottom), fill="#e5e7eb", outline="#cbd5e1", width=2)

    visible_points = [point for point in project.points if point.visible]
    if not visible_points:
        draw.text((map_left + 12, map_top + 12), "No visible points", fill="#6b7280", font=subtitle_font)
        return _encode(canvas, image_format)

    min_lon, max_lon, min_lat, max_lat = _bounds(visible_points)
    lon_span = max(max_lon - min_lon, 0.001)
    lat_span = max(max_lat - min_lat, 0.001)

    # Subject first so it always wins a label placement; other points can't push it out.
    ordered = sorted(visible_points, key=lambda p: p.symbol != "subject")
    placed_boxes: list[tuple[float, float, float, float]] = []

    for point in ordered:
        x = map_left + ((point.longitude - min_lon) / lon_span) * map_w
        y = map_bottom - ((point.latitude - min_lat) / lat_span) * map_h
        radius = max(4, int(4 * point.size)) + (2 if point.symbol == "subject" else 0)
        color = SYMBOL_COLORS.get(point.symbol, SYMBOL_COLORS["custom"])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline="#ffffff", width=2)

        box = _place_label(
            draw, _truncate(point.label, 24), label_font, x, y, radius,
            map_left, map_top, map_right, map_bottom, label_margin, placed_boxes,
        )
        if box:
            placed_boxes.append(box)

    return _encode(canvas, image_format)


def _place_label(draw, text, font, x, y, radius, left, top, right, bottom, margin, placed):
    """Try a few positions around the point; skip the label entirely rather than let it
    run off the canvas or overlap another label — an unlabeled dot beats unreadable text."""
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    gap = radius + 4
    candidates = [
        (x + gap, y - th / 2),
        (x - gap - tw, y - th / 2),
        (x - tw / 2, y + gap),
        (x - tw / 2, y - gap - th),
    ]
    for cx, cy in candidates:
        box = (cx, cy, cx + tw, cy + th)
        if box[0] < left + margin or box[2] > right - margin or box[1] < top + margin or box[3] > bottom - margin:
            continue
        if any(_overlaps(box, other) for other in placed):
            continue
        draw.text((cx, cy), text, fill="#111827", font=font)
        return box
    return None


def _overlaps(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0


def _encode(canvas: Image.Image, image_format: str) -> bytes:
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
