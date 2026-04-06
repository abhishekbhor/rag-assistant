from config.settings import EMBEDDING_PROVIDER
from app.providers.openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider():
    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider()

    raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")