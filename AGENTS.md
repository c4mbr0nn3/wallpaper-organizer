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

## Classification flow (hybrid)

Two-pass heuristic + optional AI batch classification:

1. **Heuristic** (free, instant): exact match → 1% tolerance match → aspect-ratio + height bucket match.
2. **AI batch** (if heuristic undecided): SHA256 + dimensions sent in one request to an OpenAI-compatible API. Falls back to `other/` on failure or missing config.

## AI API config (`.env`)

Place a `.env` file in the working directory with these vars:

```
AI_API_URL=https://api.openai.com/v1/chat/completions
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini          # optional, defaults to gpt-4o-mini
```

Env is loaded via `os.environ.setdefault`, so shell exports take priority. API uses [`urllib`](https://docs.python.org/3/library/urllib.request.html) + [`hashlib`](https://docs.python.org/3/library/hashlib.html) — no extra deps.

## Commit guidelines

- **Conventional Commits** — `type: subject` (e.g. `feat: add ultrawide resolution support`).
- **One line only** — no body/description.
- **Always ask** before committing or pushing.
