"""
OCR script for Christian Astrology using Google Cloud Vision API.
Extracts text from PDF preserving pagination markers.
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Por favor, instalá PyMuPDF: pip install pymupdf")
    sys.exit(1)

try:
    from google.cloud import vision
except ImportError:
    print("Por favor, instalá google-cloud-vision: pip install google-cloud-vision")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = REPO_ROOT / "astro-texts" / "Lilly_William-Christian_astrology.pdf"
OUT_PATH = REPO_ROOT / "data" / "doctrinal_corpus" / "christian_astrology_ocr.txt"

def run_ocr():
    if not PDF_PATH.exists():
        print(f"Error: No se encontró el PDF en {PDF_PATH}")
        sys.exit(1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Inicializar cliente de Vision (usa ADC automáticamente)
    client = vision.ImageAnnotatorClient()

    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count

    print(f"Iniciando OCR de {total_pages} páginas...")

    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for page_num in range(total_pages):
            current_page = page_num + 1
            print(f"[OCR] página {current_page}/{total_pages}")
            
            page = doc[page_num]
            
            # Intentar extraer texto directamente primero
            extracted_text = page.get_text()
            if extracted_text and extracted_text.strip():
                # Escribir separador y texto
                out_f.write(f"--- PAGE {current_page} ---\n")
                out_f.write(extracted_text.strip() + "\n\n")
                out_f.flush()
                sys.stdout.flush()
                continue
                
            # Si no hay texto, usar OCR
            # Render page to a pixmap at 300 DPI para textos antiguos
            pix = page.get_pixmap(dpi=300)
            
            # Convert to PNG bytes in memory
            img_bytes = pix.tobytes("png")
            
            # Send to Google Vision API
            image = vision.Image(content=img_bytes)
            # Usar document_text_detection para lectura de libros
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                print(f"Error de Vision API en página {current_page}: {response.error.message}")
                continue
                
            text = ""
            if response.full_text_annotation:
                text = response.full_text_annotation.text
                
            # Escribir separador y texto
            out_f.write(f"--- PAGE {current_page} ---\n")
            out_f.write(text.strip() + "\n\n")
            out_f.flush()
            sys.stdout.flush()

    doc.close()
    print(f"\nOCR completado. Resultados guardados en {OUT_PATH}")

if __name__ == "__main__":
    run_ocr()
