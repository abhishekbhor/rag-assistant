from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def rerank(question, chunks, top_k=3):
    scored_chunks = []

    for chunk in chunks:
        prompt = f"""
        Rate how relevant this context is to the question on a scale of 1 to 10.

        Question:
        {question}

        Context:
        {chunk['text']}

        Only return a number.
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        score = int(response.choices[0].message.content.strip())
        scored_chunks.append((score, chunk))

    # Sort by score descending
    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    return [chunk for _, chunk in scored_chunks[:top_k]]