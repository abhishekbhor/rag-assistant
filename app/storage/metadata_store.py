import pickle
import os
from config.settings import CHUNKS_PATH


def save_chunks(chunks):
    os.makedirs(os.path.dirname(CHUNKS_PATH), exist_ok=True)

    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

def load_chunks():
    with open(CHUNKS_PATH, "rb") as f:
        return pickle.load(f)