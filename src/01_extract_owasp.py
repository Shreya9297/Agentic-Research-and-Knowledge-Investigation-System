import pymupdf
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# OWASP section page ranges
# start_page and end_page are human-readable PDF page numbers
sections = [
    ("LLM01", "prompt_injection", 10, 17),
    ("LLM02", "sensitive_information_disclosure", 18, 22),
    ("LLM03", "excessive_agency", 23, 26),
    ("LLM04", "supply_chain", 27, 32),
    ("LLM05", "data_model_poisoning", 33, 37),
    ("LLM06", "unbounded_consumption", 38, 42),
    ("LLM07", "misinformation", 43, 45),
    ("LLM08", "hidden_context_exposure", 46, 49),
    ("LLM09", "vector_embedding_weaknesses", 50, 54),
    ("LLM10", "improper_output_handling", 55, 57),
]


doc = pymupdf.open(PDF_PATH)

for document_id, name, start_page, end_page in sections:

    extracted_pages = []

    for page_number in range(start_page, end_page + 1):

        # PyMuPDF uses zero-based page indexing
        page = doc[page_number - 1]

        text = page.get_text("text", sort=True)

        extracted_pages.append(
            f"\n--- SOURCE PAGE {page_number} ---\n{text}"
        )

    full_text = "\n".join(extracted_pages)

    output_file = OUTPUT_DIR / f"{document_id}_{name}.txt"

    output_file.write_text(
        full_text,
        encoding="utf-8"
    )

    print(
        f"Created {output_file.name} "
        f"(pages {start_page}-{end_page})"
    )

doc.close()

print("\nOWASP extraction completed!")