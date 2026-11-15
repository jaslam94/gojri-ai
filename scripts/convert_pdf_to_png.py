"""
Convert PDF pages to high-resolution PNG images.
Usage: py -3 scripts/convert_pdf_to_png.py
"""

import fitz  # PyMuPDF
import os
from pathlib import Path

# Configuration
PDF_PATH = Path("pdfs/anjumshanasi/Kahawat-Kosh.pdf")
OUTPUT_DIR = Path("png_pages")
DPI = 300

def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Open PDF
    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    # Convert each page
    for page_num in range(total_pages):
        page = doc[page_num]
        
        # Render at specified DPI
        mat = fitz.Matrix(DPI / 72, DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        
        # Save as PNG
        output_path = OUTPUT_DIR / f"page_{page_num + 1:04d}.png"
        pix.save(output_path)
        
        if (page_num + 1) % 10 == 0 or page_num == 0:
            print(f"Converted page {page_num + 1}/{total_pages}")
    
    doc.close()
    print(f"\nDone. PNG files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
