#!/usr/bin/env python3
"""
MedVisionAI — Sample Chest X-ray Downloader
============================================
Downloads 3 open-source chest X-ray images into /test_images/
so the upload → Grad-CAM pipeline can be tested immediately.

Sources:
  • NIH Chest X-ray 14 public samples via GitHub (CC0 licence)
  • Wikimedia Commons chest X-ray images (public domain)

Usage:
    python download_samples.py
"""

import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── Output directory ──────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "test_images"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Sample images (public domain / CC0) ──────────────────────
SAMPLES = [
    {
        "filename": "normal_chest_xray.jpg",
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "4/48/CXR_-_normal.jpg/800px-CXR_-_normal.jpg"
        ),
        "label": "Normal Chest X-ray (Wikimedia Commons — public domain)",
    },
    {
        "filename": "pneumonia_chest_xray.jpg",
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "2/2e/Pneumonias_Bacterial_Pneumonia_Cavity_with_air-fluid_level.jpg/"
            "800px-Pneumonias_Bacterial_Pneumonia_Cavity_with_air-fluid_level.jpg"
        ),
        "label": "Bacterial Pneumonia X-ray (Wikimedia Commons — public domain)",
    },
    {
        "filename": "pleural_effusion_xray.jpg",
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/"
            "f/ff/Pleural_effusion.jpg/800px-Pleural_effusion.jpg"
        ),
        "label": "Pleural Effusion X-ray (Wikimedia Commons — public domain)",
    },
]


# ── Helpers ───────────────────────────────────────────────────
def _progress_bar(count: int, total: int, prefix: str = "") -> None:
    bar_len = 40
    filled = int(bar_len * count / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = int(100 * count / total)
    print(f"\r{prefix} [{bar}] {pct}%", end="", flush=True)


class _ProgressHook:
    def __init__(self, label: str):
        self.label = label

    def __call__(self, block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            _progress_bar(min(downloaded, total_size), total_size, prefix=self.label[:30])


def download_sample(sample: dict, output_dir: Path, timeout: int = 30) -> bool:
    dest = output_dir / sample["filename"]

    if dest.exists():
        print(f"  ✓ {sample['filename']} already exists — skipping.")
        return True

    print(f"\n  ↓ Downloading: {sample['label']}")
    print(f"    URL : {sample['url']}")

    headers = {"User-Agent": "MedVisionAI/1.0 (sample downloader)"}
    req = urllib.request.Request(sample["url"], headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        _progress_bar(downloaded, total_size, prefix=f"  {sample['filename']}")

        print(f"\n    ✅ Saved → {dest}  ({dest.stat().st_size // 1024} KB)")
        return True

    except urllib.error.HTTPError as e:
        print(f"\n    ❌ HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"\n    ❌ Network error: {e.reason}")
    except Exception as e:
        print(f"\n    ❌ Unexpected error: {e}")

    # Clean up partial file
    if dest.exists():
        dest.unlink()
    return False


# ── Main ──────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  MedVisionAI — Sample Chest X-ray Downloader")
    print("=" * 60)
    print(f"  Output directory: {OUTPUT_DIR.resolve()}\n")

    success_count = 0
    for sample in SAMPLES:
        result = download_sample(sample, OUTPUT_DIR)
        if result:
            success_count += 1
        time.sleep(0.5)  # polite delay between requests

    print("\n" + "=" * 60)
    print(f"  Done — {success_count}/{len(SAMPLES)} images downloaded.")

    if success_count > 0:
        print("\n  You can now test the pipeline:")
        print("  1. Start the backend:  docker compose up backend")
        print("  2. Register a user:    POST /api/auth/register")
        print("  3. Upload a scan:      POST /api/predict  (with Bearer token)")
        print(
            f"\n  Images saved in: {OUTPUT_DIR.resolve()}"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
