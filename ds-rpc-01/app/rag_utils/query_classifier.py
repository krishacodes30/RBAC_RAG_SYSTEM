from app.llm.llm_provider import CLASSIFIER_MODELS

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_query_type_llm(question: str) -> str:
    prompt = f"""
You are a classifier that decides if a user's question should be handled by structured SQL query logic or by unstructured document search (RAG).

If the question contains terms related to **structured data analysis** (e.g., "average", "sum", "total", "count", "how many", "filter", "greater than", "less than", "top 5", "group by", "details of employee" etc.), classify it as:

→ "SQL"

If the question is more about general understanding, summarization, definitions, or cannot be answered from structured tabular data, classify it as:
If question is about summary of a document, process etc classify it as
→ "RAG"

Respond with only one word: either **SQL** or **RAG**.

Here is the question:

"{question}"

Answer:
    """

    try:

        response = None
        for model_instance in CLASSIFIER_MODELS:
            try:
                response = model_instance.invoke(prompt)
                if response and response.content:
                    break
            except Exception:
                continue

        if not response or not response.content:
            raise RuntimeError("All classifier models failed to respond.")

        result = response.content.strip().upper()


        if "SQL" in result and "RAG" not in result:
            return "SQL"

        if "RAG" in result and "SQL" not in result:
            return "RAG"


        return "RAG"

    except Exception as e:

        print(
            f"⚠️ Query classification failed: {e}"
        )

        return "RAG"