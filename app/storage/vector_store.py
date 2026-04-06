import faiss
from config.settings import INDEX_PATH

# -------------------------------
# Step 4: Store embeddings in FAISS index
# -------------------------------
def save_index(index):
    faiss.write_index(index, INDEX_PATH)

# -------------------------------
# Step 5: Load index from disk
# -------------------------------
def load_index():
    return faiss.read_index(INDEX_PATH)