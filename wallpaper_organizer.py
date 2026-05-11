#!/usr/bin/env python3
"""
Wallpaper organizer — sorts images into resolution folders.
Hybrid heuristic + AI classification. Stdlib only.

Usage: python wallpaper_organizer.py <path_to_wallpaper_folder>
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


# Heuristic canonical resolutions: (width, height, folder_name)
# Stored landscape (large, small) for normalized matching.
CANONICAL_RESOLUTIONS = [
    (1920, 1080, "1080p"),
    (2560, 1440, "1440p"),
    (3840, 2160, "4k"),
    (3440, 1440, "1440p_ultrawide"),
    (2560, 1080, "1080p_ultrawide"),
    (5120, 2160, "4k_ultrawide"),
    (1366, 768, "768p"),
    (1600, 900, "900p"),
    (1680, 1050, "1050p"),
    (2048, 1152, "1152p"),
]

# Aspect ratio + height buckets for Tier-3 heuristic.
# (aspect_ratio, height_px, folder_name)
ASPECT_BUCKETS = [
    (16 / 9, 1080, "1080p"),
    (16 / 9, 1440, "1440p"),
    (16 / 9, 2160, "4k"),
    (21 / 9, 1080, "1080p_ultrawide"),
    (21 / 9, 1440, "1440p_ultrawide"),
    (21 / 9, 2160, "4k_ultrawide"),
    (16 / 10, 768, "768p"),
    (16 / 10, 900, "900p"),
    (16 / 10, 1050, "1050p"),
    (16 / 10, 1152, "1152p"),
]

VALID_FOLDERS = {folder for _, _, folder in CANONICAL_RESOLUTIONS} | {"other"}
HEURISTIC_TOLERANCE = 0.01


AI_SYSTEM_PROMPT = (
    'You classify wallpaper images into resolution-based folders. '
    'Return a JSON object mapping each sha256 hash to one of these folder names:\n'
    '- "1080p": Standard Full HD (1920x1080)\n'
    '- "1440p": Quad HD (2560x1440)\n'
    '- "4k": Ultra HD (3840x2160)\n'
    '- "1080p_ultrawide": 21:9 ultrawide (2560x1080)\n'
    '- "1440p_ultrawide": 21:9 ultrawide (3440x1440)\n'
    '- "4k_ultrawide": 21:9 ultrawide (5120x2160)\n'
    '- "768p": 1366x768\n'
    '- "900p": 1600x900\n'
    '- "1050p": 1680x1050\n'
    '- "1152p": 2048x1152\n'
    '- "other": Anything that does not fit above\n\n'
    'Rules:\n'
    '- Consider both width and height (portrait vs landscape does not matter).\n'
    '- If dimensions are close to a known resolution (within ~2 %), classify accordingly.\n'
    '- Only use "other" for genuinely unusual aspect ratios or sizes.\n'
    '- Respond with ONLY valid JSON, no extra text.'
)


def load_env():
    """Load .env from CWD (standard OpenAI-compat keys)."""
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get_image_dimensions(image_path):
    """Get image dimensions via ImageMagick identify."""
    try:
        result = subprocess.run(
            ["identify", "-format", "%w %h", str(image_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                return (int(parts[0]), int(parts[1]))
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError,
            ValueError, FileNotFoundError):
        return None


def file_sha256(file_path):
    """SHA-256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def get_unique_filename(destination_path):
    """Append _1, _2, etc. to avoid name collisions."""
    if not destination_path.exists():
        return destination_path
    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def is_supported_image(filename):
    return Path(filename).suffix.lower() in {".jpg", ".jpeg", ".png"}


def _within_tolerance(val, target):
    return abs(val - target) / target <= HEURISTIC_TOLERANCE


def heuristic_classify(width, height):
    """
    Three-tier heuristic: exact → tolerance → aspect-ratio + height bucket.
    Returns (folder, rule_name) or (None, None) if undecided.
    """
    large = max(width, height)
    small = min(width, height)

    # Tier 1 — exact match
    for cw, ch, folder in CANONICAL_RESOLUTIONS:
        if large == cw and small == ch:
            return folder, "exact"

    # Tier 2 — tolerance match
    for cw, ch, folder in CANONICAL_RESOLUTIONS:
        if _within_tolerance(large, cw) and _within_tolerance(small, ch):
            return folder, "tolerance"

    # Tier 3 — aspect ratio + height bucket
    aspect = large / small
    for ar, h_target, folder in ASPECT_BUCKETS:
        if _within_tolerance(aspect, ar) and _within_tolerance(small, h_target):
            return folder, "aspect"

    return None, None


def _build_ai_payload(items):
    """Build OpenAI-compatible chat request body."""
    return {
        "model": os.environ.get("AI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Classify these wallpapers:\n"
                           + json.dumps(items, indent=2),
            },
        ],
    }


def ai_batch_classify(items):
    """
    Send unresolved items to OpenAI-compatible endpoint.
    items: list of dicts with keys 'sha256', 'width', 'height'
    Returns dict mapping sha256 → folder_name, or None on failure.
    """
    api_url = os.environ.get("AI_API_URL")
    api_key = os.environ.get("AI_API_KEY")
    if not api_url or not api_key:
        print("Warning: AI_API_URL or AI_API_KEY not set — skipping AI pass.")
        return None

    payload = _build_ai_payload(items)
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
            content = body["choices"][0]["message"]["content"]
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("AI response is not a JSON object")
            return result
    except Exception as e:
        print(f"Warning: AI classification failed: {e}")
        return None


def _move_file(file_path, dest_folder, filename, width, height, rule=None):
    """Move file to dest_folder, resolving name conflicts."""
    dest_folder.mkdir(exist_ok=True)
    dest_path = dest_folder / filename
    final_path = get_unique_filename(dest_path)
    shutil.move(str(file_path), str(final_path))

    if final_path != dest_path:
        print(f"  Renamed to avoid conflict: {final_path.name}")

    label = f" [{rule}]" if rule else ""
    print(f"  Moved: {filename} ({width}x{height}) -> {dest_folder.name}/{label}")


def organize_wallpapers(target_folder):
    """Main orchestrator: heuristic pass then optional AI pass."""
    target_path = Path(target_folder)

    if not target_path.exists():
        print(f"Error: Directory '{target_folder}' does not exist")
        return False
    if not target_path.is_dir():
        print(f"Error: '{target_folder}' is not a directory")
        return False

    # Verify ImageMagick
    try:
        subprocess.run(["identify", "-version"],
                       capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("Error: ImageMagick 'identify' command not found.")
        print("Install: sudo apt install imagemagick")
        return False

    print(f"Organizing wallpapers in: {target_path.absolute()}")

    files = [f for f in target_path.iterdir() if f.is_file()]
    processed = 0
    skipped = 0
    errors = 0

    # ── First pass: heuristic ──────────────────────────────────
    ai_batch = []  # (file_path, width, height, sha256)

    for file_path in files:
        filename = file_path.name

        if not is_supported_image(filename):
            if file_path.suffix.lower() in {".bmp", ".gif", ".webp",
                                             ".tiff", ".svg"}:
                print(f"  Warning: unsupported format: {filename}")
            skipped += 1
            continue

        dims = get_image_dimensions(file_path)
        if dims is None:
            print(f"  Warning: could not read dimensions: {filename}")
            errors += 1
            continue

        width, height = dims
        folder, rule = heuristic_classify(width, height)

        if folder:
            _move_file(file_path, target_path / folder,
                       filename, width, height, rule)
            processed += 1
        else:
            sha = file_sha256(file_path)
            ai_batch.append((file_path, width, height, sha, filename))

    # ── Second pass: AI batch ──────────────────────────────────
    if ai_batch:
        items_for_api = [
            {"sha256": sha, "width": w, "height": h}
            for _, w, h, sha, _ in ai_batch
        ]
        results = ai_batch_classify(items_for_api)

        for file_path, width, height, sha, filename in ai_batch:
            folder = "other"
            rule = None
            if results and sha in results:
                candidate = results[sha]
                if candidate in VALID_FOLDERS:
                    folder = candidate
                    rule = "ai"

            _move_file(file_path, target_path / folder,
                       filename, width, height, rule)
            processed += 1

    print(f"\nSummary: {processed} processed, {skipped} skipped, "
          f"{errors} errors")
    return True


def main():
    load_env()

    if len(sys.argv) != 2:
        print("Usage: python wallpaper_organizer.py <path_to_wallpaper_folder>")
        sys.exit(1)

    if not organize_wallpapers(sys.argv[1]):
        sys.exit(1)


if __name__ == "__main__":
    main()
