import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_FILE = PROJECT_ROOT / "data" / "chunks" / "owasp_chunks.json"

OUTPUT_DIR = PROJECT_ROOT / "data" / "embeddings"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_FILE = OUTPUT_DIR / "owasp_embeddings.npy"


# --------------------------------------------------
# Load chunks
# --------------------------------------------------

with CHUNKS_FILE.open("r", encoding="utf-8") as f:
    chunks = json.load(f)

print("Chunks loaded:", len(chunks))


# --------------------------------------------------
# Extract text
# --------------------------------------------------

texts = [chunk["text"] for chunk in chunks]


# --------------------------------------------------
# Load Sentence Transformer
# --------------------------------------------------

print("\nLoading all-MiniLM-L6-v2...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# --------------------------------------------------
# Generate embeddings
# --------------------------------------------------

print("Creating embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True
)


# --------------------------------------------------
# Save embeddings
# --------------------------------------------------

np.save(EMBEDDINGS_FILE, embeddings)


print("\n----------------------------------")
print("Embedding generation completed!")
print("----------------------------------")

print("Number of chunks:", len(chunks))
print("Embedding shape:", embeddings.shape)
print("Saved to:", EMBEDDINGS_FILE)