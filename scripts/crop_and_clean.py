"""
Crop margins and remove blank pages from PNG images.
Usage: py -3 scripts/crop_and_clean.py
"""

from PIL import Image
import numpy as np
from pathlib import Path

# Configuration
INPUT_DIR = Path("png_pages")
OUTPUT_DIR = Path("cropped_pages")
BLANK_THRESHOLD = 0.02  # Pages with less than 2% content are considered blank
WHITE_THRESHOLD = 250   # Pixels above this value are considered "white"

def find_content_bounds(img_array):
    """Find the bounding box of non-white content."""
    # Create mask of non-white pixels
    mask = np.any(img_array < WHITE_THRESHOLD, axis=2)
    
    # Find content bounds
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        return None  # Blank page
    
    row_indices = np.where(rows)[0]
    col_indices = np.where(cols)[0]
    
    top = row_indices[0]
    bottom = row_indices[-1] + 1
    left = col_indices[0]
    right = col_indices[-1] + 1
    
    return (left, top, right, bottom)

def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Get all PNG files
    png_files = sorted(INPUT_DIR.glob("*.png"))
    if not png_files:
        print(f"No PNG files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(png_files)} PNG files")
    
    blank_count = 0
    cropped_count = 0
    
    for i, png_path in enumerate(png_files):
        # Load image
        img = Image.open(png_path)
        img_array = np.array(img)
        
        # Find content bounds
        bounds = find_content_bounds(img_array)
        
        if bounds is None:
            # Skip blank page
            print(f"Skipping blank page: {png_path.name}")
            blank_count += 1
            continue
        
        # Crop to content
        cropped = img.crop(bounds)
        
        # Save cropped image
        output_path = OUTPUT_DIR / png_path.name
        cropped.save(output_path)
        
        cropped_count += 1
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(png_files)} pages")
    
    print(f"\nDone.")
    print(f"Total pages: {len(png_files)}")
    print(f"Cropped and saved: {cropped_count}")
    print(f"Blank pages removed: {blank_count}")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
