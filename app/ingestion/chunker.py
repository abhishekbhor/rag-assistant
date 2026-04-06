def chunk_text(text, chunk_size=500, overlap=100, source="docs.txt"):
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk_str = text[start:end].strip()

        if len(chunk_str) < 50:
            break

        chunks.append({
            "id": chunk_id,
            "text": chunk_str,
            "source": source,
            "chunk_index": chunk_id
        })

        chunk_id += 1
        start += chunk_size - overlap

    return chunks