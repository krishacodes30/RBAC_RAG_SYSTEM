from openai import OpenAI
import os


from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load variables from .env
load_dotenv()


# Get Gemini API key from .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing from .env")


# Create Gemini chat model
model = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    temperature=0,
    max_retries=2,
    google_api_key=GOOGLE_API_KEY
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    response = model.invoke(prompt)
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0
    # )
    result = response.content.strip().upper()

    return result