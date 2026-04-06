from app.providers.factory import get_embedding_provider

provider = get_embedding_provider()

def embed_query(question: str):
    return provider.embed(question)