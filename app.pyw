import ctypes
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
WALLPAPERS_DIR = BASE_DIR / "wallpapers"
CACHE_DIR = BASE_DIR / ".cache"
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}

CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def prepare_wallpaper(path: Path) -> Path:
    """Converts the image to JPEG if needed (Windows handles native PNGs poorly)."""
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return path
    cached = CACHE_DIR / (path.stem + ".jpg")
    # Only reconvert if the source is newer than the cache
    if not cached.exists() or path.stat().st_mtime > cached.stat().st_mtime:
        img = Image.open(path).convert("RGB")
        img.save(cached, "JPEG", quality=95)
    return cached


def set_wallpaper(path: Path) -> bool:
    ready = prepare_wallpaper(path)
    abs_path = str(ready.resolve())
    return bool(ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, abs_path, 0x03))


def parse_schedules() -> list[tuple[int, int, Path]]:
    """
    Scans wallpapers/ and returns a sorted list of (hour, minute, path).
    Filename must be HH,MM (e.g. 09,00.jpg or 21,30.png).
    """
    schedules = []
    if not WALLPAPERS_DIR.exists():
        return schedules

    for f in WALLPAPERS_DIR.iterdir():
        if f.suffix.lower() not in SUPPORTED_EXT:
            continue
        stem = f.stem  # e.g. "09,00"
        parts = stem.split(",")
        if len(parts) != 2:
            continue
        try:
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                schedules.append((h, m, f))
        except ValueError:
            continue

    schedules.sort(key=lambda x: (x[0], x[1]))
    return schedules


def get_current_wallpaper(schedules: list[tuple[int, int, Path]]) -> Path | None:
    """
    Returns the currently active image (the last scheduled time that has passed today).
    Handles midnight wrap-around (falls back to the last entry if none have triggered yet).
    """
    if not schedules:
        return None

    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    active = None
    for h, m, path in schedules:
        if h * 60 + m <= current_minutes:
            active = path

    # Wrap-around: if no image has triggered yet today, use the last one
    if active is None:
        active = schedules[-1][2]

    return active


def seconds_until_next(schedules: list[tuple[int, int, Path]]) -> tuple[float, Path | None]:
    """
    Computes the number of seconds until the next wallpaper change.
    Returns (seconds, next_image).
    """
    if not schedules:
        return 3600.0, None

    now = datetime.now()
    current_seconds = now.hour * 3600 + now.minute * 60 + now.second

    for h, m, path in schedules:
        target_seconds = h * 3600 + m * 60
        if target_seconds > current_seconds:
            return float(target_seconds - current_seconds), path

    # Wrap-around: next occurrence is the first entry of tomorrow
    first_h, first_m, first_path = schedules[0]
    seconds_in_day = 24 * 3600
    target_seconds = first_h * 3600 + first_m * 60
    remaining = seconds_in_day - current_seconds + target_seconds
    return float(remaining), first_path


# ---------------------------------------------------------------------------
# Systray icon (dynamically generated)
# ---------------------------------------------------------------------------

def make_tray_icon() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background circle
    draw.ellipse([4, 4, 60, 60], fill=(30, 30, 30, 220))
    # Symbolic clock hands
    draw.line([32, 32, 32, 14], fill=(255, 255, 255), width=3)
    draw.line([32, 32, 46, 40], fill=(255, 200, 50), width=3)
    draw.ellipse([28, 28, 36, 36], fill=(255, 255, 255))
    return img


# ---------------------------------------------------------------------------
# Main scheduler thread
# ---------------------------------------------------------------------------

class WallpaperScheduler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        # Apply the correct wallpaper immediately on startup
        schedules = parse_schedules()
        current = get_current_wallpaper(schedules)
        if current:
            set_wallpaper(current)

        while not self._stop_event.is_set():
            schedules = parse_schedules()
            wait_secs, next_image = seconds_until_next(schedules)

            # Sleep exactly until the next change; wake every 60s max as a safety net
            slept = 0.0
            while slept < wait_secs and not self._stop_event.is_set():
                chunk = min(60.0, wait_secs - slept)
                self._stop_event.wait(timeout=chunk)
                slept += chunk

            if self._stop_event.is_set():
                break

            # Re-parse to pick up any changes made to the wallpapers folder
            schedules = parse_schedules()
            current = get_current_wallpaper(schedules)
            if current:
                set_wallpaper(current)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    scheduler = WallpaperScheduler()
    scheduler.start()

    icon_image = make_tray_icon()

    def on_quit(icon, item):
        scheduler.stop()
        icon.stop()

    def on_apply_now(icon, item):
        schedules = parse_schedules()
        current = get_current_wallpaper(schedules)
        if current:
            set_wallpaper(current)

    menu = pystray.Menu(
        pystray.MenuItem("Apply now", on_apply_now),
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon("Timepaper", icon_image, "Timepaper", menu)
    icon.run()


if __name__ == "__main__":
    main()
