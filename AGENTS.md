# wallpaper-organizer

Single-file Python script that sorts wallpapers into resolution-named folders.

## How to run

```sh
python wallpaper_organizer.py <path_to_wallpaper_folder>
```

## Key facts

- **Stdlib only** — no `pip install`, no venv, no package manifest.
- **Prerequisite: ImageMagick `identify`** — verify with `identify -version`. Install on Ubuntu: `sudo apt install imagemagick`.
- **Files are MOVED**, not copied. Irreversible.
- **Only root-level files processed** — no recursion into subdirectories.
- **Supported extensions**: `.jpg`, `.jpeg`, `.png` (case-insensitive). Other image formats silently skipped.
- **Exit code 1** on: missing target dir, ImageMagick unavailable, processing failure.
- **No tests, no lint, no CI.** Nothing to build.
- **MIT License** — Francesco Zorzi, 2025.

## Commit guidelines

- **Conventional Commits** — `type: subject` (e.g. `feat: add ultrawide resolution support`).
- **One line only** — no body/description.
- **Always ask** before committing or pushing.
