from app.services.ingestion_service import run_ingestion_pipeline
from app.services.query_service import run_query_pipeline


def run_ingestion():
    result = run_ingestion_pipeline()
    print(result)


def run_query():
    question = input("Ask a question: ")
    result = run_query_pipeline(question, include_debug=True)

    print("\nAnswer:\n", result["answer"])
    print("\nSources:\n")
    for i, chunk in enumerate(result["sources"]):
        print(f"[{i+1}] Source: {chunk['source']} | Chunk: {chunk['chunk_index']}")
        print(chunk["preview"], "\n")

    if "debug" in result:
        print("\nDebug:\n", result["debug"])


if __name__ == "__main__":
    mode = input("ingest or query: ").strip().lower()

    if mode == "ingest":
        run_ingestion()
    elif mode == "query":
        run_query()