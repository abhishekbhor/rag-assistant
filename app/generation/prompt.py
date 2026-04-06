def build_prompt(question, context_chunks):
    context = "\n\n".join([chunk["text"] for chunk in context_chunks])

    return f"""
Answer ONLY using the provided context.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question:
{question}
"""