# Wallpaper Organizer

A Python script that automatically organizes wallpaper images into folders based on their resolution. Perfect for keeping your wallpaper collection tidy and easily browsable.

## Features

- 🖼️ Automatically detects image resolutions
- 📁 Creates organized folders by resolution (1080p, 1440p, 4K, etc.)
- ⚡ Fast processing using ImageMagick
- 🤖 Hybrid classification: heuristic pre-filter (flexible tolerance) + optional AI batch via OpenAI-compatible API
- 🔄 Handles filename conflicts automatically
- 📝 Detailed console output with progress and warnings
- 🛡️ Safe file handling with error recovery

## Dependencies

The script requires **ImageMagick** to be installed on your system for reliable image dimension detection.

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install imagemagick
```

### Other Linux distributions
- **CentOS/RHEL/Fedora**: `sudo yum install ImageMagick` or `sudo dnf install ImageMagick`
- **Arch Linux**: `sudo pacman -S imagemagick`

### Verify installation
```bash
identify -version
```

## Supported Image Formats

- **JPEG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)

Other formats (`.bmp`, `.gif`, `.webp`, `.tiff`, `.svg`) will be skipped with a warning message.

## Classification (How folders are chosen)

The script uses a two-pass hybrid approach — no API key required unless you want AI help.

### Pass 1 — Heuristic (free, instant)
1. **Exact match** against known resolutions
2. **1% tolerance match** for near-miss dimensions
3. **Aspect-ratio + height bucket** fallback

If a match is found, the file is moved immediately.

### Pass 2 — AI batch (optional)
Files the heuristic cannot resolve are batched together. If `AI_API_URL` and `AI_API_KEY` are set via `.env` or environment variables, the batch is sent to an OpenAI-compatible API in a single request. Each result is validated against known folders. On any failure (network, parsing, missing config), files fall back to `other/`.

## Supported Resolutions

The script automatically categorizes images into the following folders:

### Standard Resolutions
- **768p** - 1366×768
- **900p** - 1600×900
- **1050p** - 1680×1050
- **1080p** - 1920×1080 (includes portrait: 1080×1920)
- **1152p** - 2048×1152
- **1440p** - 2560×1440 (includes portrait: 1440×2560)
- **4k** - 3840×2160 (includes portrait: 2160×3840)

### Ultrawide Resolutions
- **1080p_ultrawide** - 2560×1080
- **1440p_ultrawide** - 3440×1440
- **4k_ultrawide** - 5120×2160

### Non-standard Resolutions
- **other** - Any resolution not matching the above categories

## Installation & Setup

1. **Clone or download** this repository
2. **Install ImageMagick** (see Dependencies section above)
3. **Make the script executable** (optional):
   ```bash
   chmod +x wallpaper_organizer.py
   ```
4. **(Optional) AI classification** — create a `.env` file in the working directory:
   ```bash
   AI_API_URL=https://api.openai.com/v1/chat/completions
   AI_API_KEY=sk-...
   AI_MODEL=gpt-4o-mini
   ```
   The script works without this; only unresolved files use the API when configured.

## Standalone binary (portable)

Bundle into a single executable with **PyInstaller** — no Python or deps needed on the target machine:

```bash
pipx install pyinstaller
pyinstaller --onefile wallpaper_organizer.py
```

The binary is at `dist/wallpaper_organizer` (Linux) or `dist/wallpaper_organizer.exe` (Windows). Copy it to any machine with ImageMagick installed and run:

```bash
./wallpaper_organizer /path/to/wallpaper/folder
```

> **Note:** ImageMagick (`identify`) must still be installed on each machine. PyInstaller only bundles the Python code, not external system tools.

## How to Run

### Basic Usage
```bash
python wallpaper_organizer.py /path/to/wallpaper/folder
```

### Run from within the wallpaper folder
```bash
# Place the script in your wallpaper folder, then:
python wallpaper_organizer.py .
```

### Examples
```bash
# Organize wallpapers in a specific directory
python wallpaper_organizer.py ~/Pictures/Wallpapers

# Organize wallpapers in current directory
python wallpaper_organizer.py .

# Organize wallpapers with full path
python wallpaper_organizer.py /home/user/Downloads/wallpapers
```

## Example Output

### Before
```
wallpapers/
├── wallpaper_organizer.py
├── sunset_beach.jpg (1920×1080)
├── mountain_view.png (2560×1440)
├── city_night.jpg (3440×1440)
└── space_nebula.jpg (3840×2160)
```

### After
```
wallpapers/
├── wallpaper_organizer.py
├── 1080p/
│   └── sunset_beach.jpg
├── 1440p/
│   └── mountain_view.png
├── 1440p_ultrawide/
│   └── city_night.jpg
└── 4k/
    └── space_nebula.jpg
```

### Console Output
```
Organizing wallpapers in: /home/user/Pictures/wallpapers
Moved: sunset_beach.jpg (1920x1080) -> 1080p/
Moved: mountain_view.png (2560x1440) -> 1440p/
Moved: city_night.jpg (3440x1440) -> 1440p_ultrawide/
Moved: space_nebula.jpg (3840x2160) -> 4k/

Summary:
  Processed: 4 files
  Skipped: 1 files
  Errors: 0 files
```

## Behavior Details

### File Processing
- **Files are moved, not copied** from the source location to resolution folders
- **Only processes files in the root directory** - ignores subdirectories
- **Creates folders only when needed** - empty resolution folders are not created
- **Processes only supported image formats** - other files are skipped

### Filename Conflicts
When a file with the same name already exists in the destination folder:
- A copy is created with an incremental number: `image.jpg` → `image_1.jpg`
- A warning is displayed in the console
- The original file in the destination remains untouched

### Error Handling
- **Corrupted images**: Skipped with warning message
- **Unsupported formats**: Image formats are warned, other files skipped silently
- **Permission errors**: Reported with error message
- **Non-standard resolutions**: Automatically moved to "other" folder

## Troubleshooting

### "ImageMagick 'identify' command not found"
**Solution**: Install ImageMagick using the commands in the Dependencies section.

### "Permission denied" errors
**Solutions**:
- Check file/folder permissions: `ls -la`
- Run with appropriate permissions or change file ownership
- Ensure the target directory is writable

### "Could not read dimensions" warnings
**Possible causes**:
- Corrupted image files
- Unsupported image variants
- File permission issues

**Solution**: These files are automatically skipped. Check the file manually or try opening it in an image viewer.

### Script processes itself
**Behavior**: The Python script file is automatically skipped (silently) as it's not a supported image format.

### No files processed
**Check**:
- Are there supported image files (jpg, jpeg, png) in the target directory?
- Are the files in the root directory (not in subdirectories)?
- Do you have read permissions for the files?

## Limitations

- **Image formats**: Only supports JPEG and PNG files
- **Directory scope**: Only processes files in the root directory, not subdirectories
- **External dependency**: Requires ImageMagick to be installed
- **File operation**: Moves files (doesn't create copies)
- **Resolution detection**: Uses flexible heuristic + optional AI (OpenAI-compatible API)

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this script.

## License

This project is open source and available under the [MIT License](LICENSE).
