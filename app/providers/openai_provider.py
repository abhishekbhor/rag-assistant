from openai import OpenAI
from config.settings import OPENAI_API_KEY, EMBEDDING_MODEL

class OpenAIEmbeddingProvider:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def embed(self, text: str):
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding