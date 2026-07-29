from pathlib import Path
import fitz  # PyMuPDF
import sys

pdf_path = Path(sys.argv[1])

doc = fitz.open(pdf_path)

for i, page in enumerate(doc, start=1):
    text = page.get_text("text")
    print(f"\n{'='*80}")
    print(f"PAGE {i}")
    print(f"{'='*80}")
    print(text[:4000])  # primeras 4000 letras