from app.ingestion.loader import load_documents
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import create_embeddings
from app.ingestion.indexer import build_index
from app.storage.vector_store import save_index
from app.storage.metadata_store import save_chunks


def run_ingestion_pipeline():
    text = load_documents()
    chunks = chunk_text(text)
    embeddings = create_embeddings(chunks)
    index = build_index(embeddings)

    save_index(index)
    save_chunks(chunks)

    return {
        "status": "success",
        "num_chunks": len(chunks)
    }