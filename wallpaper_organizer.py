#!/usr/bin/env python3
"""
Wallpaper organizer script - organizes images by resolution into folders
Usage: python wallpaper_organizer.py <path_to_wallpaper_folder>
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_image_dimensions(image_path):
    """
    Get image dimensions using ImageMagick's identify command
    Returns (width, height) or None if file is corrupted/unreadable
    """
    try:
        # Use identify to get image dimensions
        result = subprocess.run(
            ['identify', '-format', '%w %h', str(image_path)],
            capture_output=True,
            text=True,
            timeout=10  # Timeout after 10 seconds
        )
        
        if result.returncode == 0:
            dimensions = result.stdout.strip().split()
            if len(dimensions) == 2:
                width = int(dimensions[0])
                height = int(dimensions[1])
                return (width, height)
        
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None

def get_resolution_folder(width, height):
    """
    Determine the appropriate folder name based on resolution
    """
    # Standard 16:9 resolutions
    if width == 1920 and height == 1080:
        return "1080p"
    elif width == 2560 and height == 1440:
        return "1440p"
    elif width == 3840 and height == 2160:
        return "4k"
    
    # Common variations and portrait modes
    elif (width == 1080 and height == 1920) or (width == 1920 and height == 1080):
        return "1080p"
    elif (width == 1440 and height == 2560) or (width == 2560 and height == 1440):
        return "1440p"
    elif (width == 2160 and height == 3840) or (width == 3840 and height == 2160):
        return "4k"
    
    # Ultrawide variants
    elif width == 3440 and height == 1440:
        return "1440p_ultrawide"
    elif width == 2560 and height == 1080:
        return "1080p_ultrawide"
    elif width == 5120 and height == 2160:
        return "4k_ultrawide"
    
    # Other common resolutions
    elif width == 1366 and height == 768:
        return "768p"
    elif width == 1600 and height == 900:
        return "900p"
    elif width == 1680 and height == 1050:
        return "1050p"
    elif width == 2048 and height == 1152:
        return "1152p"
    
    # Everything else goes to "other"
    else:
        return "other"

def get_unique_filename(destination_path):
    """
    Generate a unique filename if file already exists
    """
    if not destination_path.exists():
        return destination_path
    
    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 1
    
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def is_supported_image(filename):
    """
    Check if file is a supported image format
    """
    supported_extensions = {'.jpg', '.jpeg', '.png'}
    return Path(filename).suffix.lower() in supported_extensions

def organize_wallpapers(target_folder):
    """
    Main function to organize wallpapers
    """
    target_path = Path(target_folder)
    
    if not target_path.exists():
        print(f"Error: Directory '{target_folder}' does not exist")
        return False
    
    if not target_path.is_dir():
        print(f"Error: '{target_folder}' is not a directory")
        return False
    
    # Check if identify command is available
    try:
        subprocess.run(['identify', '-version'], capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("Error: ImageMagick 'identify' command not found.")
        print("Please install ImageMagick: sudo apt install imagemagick")
        return False
    
    print(f"Organizing wallpapers in: {target_path.absolute()}")
    
    # Get all files in the root directory only
    files = [f for f in target_path.iterdir() if f.is_file()]
    
    processed = 0
    skipped = 0
    errors = 0
    
    for file_path in files:
        filename = file_path.name
        
        # Skip non-image files silently
        if not is_supported_image(filename):
            if file_path.suffix.lower() in {'.bmp', '.gif', '.webp', '.tiff', '.svg'}:
                print(f"Warning: Skipping unsupported format: {filename}")
            skipped += 1
            continue
        
        # Get image dimensions
        dimensions = get_image_dimensions(file_path)
        if dimensions is None:
            print(f"Warning: Could not read dimensions for {filename} (corrupted or unsupported)")
            errors += 1
            continue
        
        width, height = dimensions
        resolution_folder = get_resolution_folder(width, height)
        
        # Create resolution folder if it doesn't exist
        dest_folder = target_path / resolution_folder
        dest_folder.mkdir(exist_ok=True)
        
        # Determine destination path
        dest_path = dest_folder / filename
        final_dest_path = get_unique_filename(dest_path)
        
        try:
            # Move the file
            shutil.move(str(file_path), str(final_dest_path))
            
            if final_dest_path != dest_path:
                print(f"Warning: File renamed to avoid conflict: {filename} -> {final_dest_path.name}")
            
            print(f"Moved: {filename} ({width}x{height}) -> {resolution_folder}/")
            processed += 1
            
        except Exception as e:
            print(f"Error moving {filename}: {e}")
            errors += 1
    
    print(f"\nSummary:")
    print(f"  Processed: {processed} files")
    print(f"  Skipped: {skipped} files")
    print(f"  Errors: {errors} files")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python wallpaper_organizer.py <path_to_wallpaper_folder>")
        sys.exit(1)
    
    target_folder = sys.argv[1]
    
    if not organize_wallpapers(target_folder):
        sys.exit(1)

if __name__ == "__main__":
    main()