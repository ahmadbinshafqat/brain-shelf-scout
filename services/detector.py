from collections import deque
from pathlib import Path

from PIL import Image

from services.catalog import nearest_catalog_book


def detect_books(image_path: Path):
    """Detect vertical, saturated spine-like regions and map colors to catalog titles."""
    img = Image.open(image_path).convert("RGB")
    original_w, original_h = img.size
    max_w = 900
    if original_w > max_w:
        ratio = max_w / original_w
        img = img.resize((max_w, int(original_h * ratio)))
    w, h = img.size
    px = img.load()

    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if max(r, g, b) - min(r, g, b) > 55 and sum((r, g, b)) / 3 < 230:
                mask[y][x] = True

    visited = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(h):
        for x in range(w):
            if not mask[y][x] or visited[y][x]:
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            xs, ys = [], []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            bw, bh = x2 - x1 + 1, y2 - y1 + 1
            area = bw * bh
            if bh >= 55 and bw >= 22 and bh / max(bw, 1) >= 1.15 and area >= 1600:
                boxes.append((x1, y1, x2, y2))

    boxes = merge_overlapping(boxes)
    rows = assign_rows(boxes)
    detected = []
    scale_x = original_w / w
    scale_y = original_h / h

    for idx, box in enumerate(sorted(boxes, key=lambda b: (rows[b], b[0]))):
        x1, y1, x2, y2 = box
        rgb = average_color(img, box)
        cat, confidence = nearest_catalog_book(rgb)
        detected.append({
            "title": cat["title"],
            "author": cat["author"],
            "confidence": confidence,
            "x": int(x1 * scale_x),
            "y": int(y1 * scale_y),
            "shelf_row": rows[box] + 1,
        })

    return detected


def average_color(img, box):
    x1, y1, x2, y2 = box
    pixels = []
    for y in range(y1 + 3, y2 - 2, max(1, (y2 - y1) // 30)):
        for x in range(x1 + 3, x2 - 2, max(1, (x2 - x1) // 10)):
            pixels.append(img.getpixel((x, y)))
    if not pixels:
        return (128, 128, 128)
    return tuple(int(sum(p[i] for p in pixels) / len(pixels)) for i in range(3))


def merge_overlapping(boxes):
    boxes = sorted(boxes)
    merged = []
    for box in boxes:
        if not merged:
            merged.append(box)
            continue
        ax1, ay1, ax2, ay2 = merged[-1]
        bx1, by1, bx2, by2 = box
        horizontal_touch = bx1 <= ax2 + 8
        vertical_overlap = min(ay2, by2) - max(ay1, by1) > 20
        if horizontal_touch and vertical_overlap:
            merged[-1] = (min(ax1, bx1), min(ay1, by1), max(ax2, bx2), max(ay2, by2))
        else:
            merged.append(box)
    return merged


def assign_rows(boxes):
    centers = sorted([(b[1] + b[3]) / 2 for b in boxes])
    row_centers = []
    for c in centers:
        if not row_centers or abs(c - row_centers[-1]) > 90:
            row_centers.append(c)
        else:
            row_centers[-1] = (row_centers[-1] + c) / 2
    return {b: min(range(len(row_centers)), key=lambda i: abs(((b[1] + b[3]) / 2) - row_centers[i])) for b in boxes}
