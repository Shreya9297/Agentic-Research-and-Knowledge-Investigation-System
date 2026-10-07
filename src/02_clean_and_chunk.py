import json
import re
from pathlib import Path


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "chunks"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# DOCUMENT METADATA
# ---------------------------------------------------------

DOCUMENT_INFO = {
    "LLM01": "Prompt Injection",
    "LLM02": "Sensitive Information Disclosure",
    "LLM03": "Excessive Agency",
    "LLM04": "Supply Chain",
    "LLM05": "Data and Model Poisoning",
    "LLM06": "Unbounded Consumption",
    "LLM07": "Misinformation",
    "LLM08": "Hidden Context Exposure",
    "LLM09": "Vector and Embedding Weaknesses",
    "LLM10": "Improper Output Handling",
}


# ---------------------------------------------------------
# CLEAN TEXT
# ---------------------------------------------------------

def clean_text(text):
    """
    Perform basic cleanup while preserving the actual
    OWASP content.
    """

    # Remove repeated OWASP page header/footer
    text = re.sub(r"genai\.owasp\.org\s*", "", text)

    # Remove excessive spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------
# CHUNK TEXT
# ---------------------------------------------------------

def create_chunks(text, chunk_size=1200, overlap=200):
    """
    Divide text into overlapping character-based chunks.

    chunk_size = maximum approximate characters per chunk
    overlap = characters repeated between adjacent chunks
    """

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        # Try not to cut directly in the middle of a sentence.
        if end < len(text):

            last_period = chunk.rfind(". ")

            if last_period > chunk_size * 0.6:
                end = start + last_period + 1
                chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        # Prevent infinite loop
        new_start = end - overlap

        if new_start <= start:
            new_start = end

        start = new_start

    return chunks


# ---------------------------------------------------------
# PROCESS DOCUMENTS
# ---------------------------------------------------------

all_chunks = []

for file_path in sorted(INPUT_DIR.glob("LLM*.txt")):

    document_id = file_path.name.split("_")[0]

    topic = DOCUMENT_INFO.get(document_id, "Unknown")

    print(f"\nProcessing: {file_path.name}")
    print(f"Topic: {topic}")

    raw_text = file_path.read_text(encoding="utf-8")

    cleaned_text = clean_text(raw_text)

    chunks = create_chunks(cleaned_text)

    print(f"Chunks created: {len(chunks)}")

    for index, chunk_text in enumerate(chunks, start=1):

        chunk_record = {
            "chunk_id": f"{document_id}_CHUNK_{index:03d}",
            "document_id": document_id,
            "topic": topic,
            "source": "OWASP",
            "source_document": file_path.name,
            "text": chunk_text
        }

        all_chunks.append(chunk_record)


# ---------------------------------------------------------
# SAVE DATASET
# ---------------------------------------------------------

output_file = OUTPUT_DIR / "owasp_chunks.json"

with output_file.open("w", encoding="utf-8") as f:

    json.dump(
        all_chunks,
        f,
        indent=2,
        ensure_ascii=False
    )


print("\n----------------------------------")
print("Chunking completed!")
print("----------------------------------")
print(f"Total chunks: {len(all_chunks)}")
print(f"Saved to: {output_file}")