from rank_bm25 import BM25Okapi

def build_bm25_index(chunks):
    """
    Builds a BM25 index from chunk texts
    """

    # Tokenize text (simple split for now)
    tokenized_corpus = [chunk["text"].split() for chunk in chunks]

    bm25 = BM25Okapi(tokenized_corpus)

    return bm25, tokenized_corpus


def bm25_search(bm25, tokenized_corpus, query, k=5):
    tokenized_query = query.split()

    scores = bm25.get_scores(tokenized_query)

    # Get top-k indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    return top_indices