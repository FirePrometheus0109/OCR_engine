import json
import fitz  # PyMuPDF
from geometry import BoundingBox
import math
from typing import Dict, List, Any

# Function to make the PDF document searchable
def make_pdf_doc_searchable(
    pdf_doc: fitz.Document,
    textract_pages: List[Dict[str, Any]],
    add_word_bbox: bool = False,
    show_selectable_char: bool = False,
    pdf_image_dpi: int = 100,  # Reduced DPI
    verbose: bool = False,
) -> fitz.Document:
    # Create a new PDF for the output
    output_pdf = fitz.open()
    
    # Iterate over each page and add text overlay
    for page_number, page in enumerate(textract_pages):
        # Open the original page
        pdf_page = pdf_doc[page_number]
        
        # Create a new page with the same size
        output_page = output_pdf.new_page(width=pdf_page.rect.width, height=pdf_page.rect.height)

        # Copy original page content to the new page
        output_page.show_pdf_page(pdf_page.rect, pdf_doc, page_number)

        blocks = page.get("Blocks", [])
        for blocki, block in enumerate(blocks):
            if block["BlockType"] == "WORD":
                if verbose and blocki % 1000 == 0:
                    print(f"Processing block {blocki} on page {page_number + 1}")

                # Get the bbox object and scale it to the page pixel size
                bbox = BoundingBox.from_textract_bbox(block["Geometry"]["BoundingBox"])
                bbox.scale(output_page.rect.width, output_page.rect.height)

                # Add overlay text
                text = block["Text"]
                text_length = fitz.get_text_length(
                    text, fontname="helv", fontsize=12
                )
                fontsize_optimal = int(
                    math.floor((bbox.width / text_length) * 12)
                )
                output_page.insert_text(
                    point=fitz.Point(bbox.left, bbox.bottom),  # bottom-left of 1st char
                    text=text,
                    fontname="helv",  # the default font
                    fontsize=fontsize_optimal,
                    rotate=0,
                    color=(0, 0, 0),  # black text
                    fill_opacity=1 if show_selectable_char else 0,
                )

    pdf_doc.close()
    return output_pdf

# Main section
doc = fitz.open("input.pdf")
data = json.load(open("response.json"))

print(f"Number of pages: {len(data)}")

num_word_blocks = sum(
    1 for page in data for blk in page.get("Blocks", []) if blk["BlockType"] == "WORD"
)
print(f"Number of WORD blocks: {num_word_blocks}")

selectable_pdf_doc = make_pdf_doc_searchable(
    pdf_doc=doc,
    textract_pages=data,
    add_word_bbox=True,
    show_selectable_char=False,
    pdf_image_dpi=100,  # Reduced DPI
    verbose=True,
)

selectable_pdf_doc.save("output.pdf")