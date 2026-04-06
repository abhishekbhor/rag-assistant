import numpy as np
from config.settings import TOP_K

def search(index, query_embedding, k=TOP_K):
    query_vector = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query_vector, k)
    return indices[0]