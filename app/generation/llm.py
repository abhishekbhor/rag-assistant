from openai import OpenAI
from config.settings import OPENAI_API_KEY, LLM_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# Step 9: Generate answer using LLM
# -------------------------------
def generate_answer(prompt):
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content