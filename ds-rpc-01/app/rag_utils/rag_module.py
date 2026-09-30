from pathlib import Path
import os
import pandas as pd

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.llm.llm_provider import (
    RAG_MODELS,
    RAG_MODEL
)

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[2]

ENV_FILE = BASE_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_FILE
)


print("✅ .env loaded successfully")
print(f"✅ .env location: {ENV_FILE}")
# ============================================================
# FILE LOADING
# ============================================================

def load_file(filepath, role):
    """
    Load CSV or Markdown file and convert it into
    LangChain Document objects.
    """

    ext = Path(filepath).suffix.lower()

    try:

        # ----------------------------------------------------
        # CSV FILE
        # ----------------------------------------------------

        if ext == ".csv":

            df = pd.read_csv(filepath)

            documents = []

            for row in df.to_dict(orient="records"):

                content = "\n".join(
                    f"{key}: {value}"
                    for key, value in row.items()
                )

                documents.append(
                    Document(
                        page_content=content,
                        metadata={
                            "role": role.lower(),
                            "source": Path(filepath).name
                        }
                    )
                )

            return documents


        # ----------------------------------------------------
        # MARKDOWN FILE
        # ----------------------------------------------------

        elif ext == ".md":

            with open(
                filepath,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            return [
                Document(
                    page_content=content,
                    metadata={
                        "role": role.lower(),
                        "source": Path(filepath).name
                    }
                )
            ]


        # ----------------------------------------------------
        # UNSUPPORTED FILE
        # ----------------------------------------------------

        else:

            return None


    except Exception as e:

        print(
            f"Failed to process {filepath}: {e}"
        )

        return None


# ============================================================
# GEMINI CHAT MODELS
# ============================================================

# RAG_MODEL = os.getenv(
#     "RAG_MODEL",
#     "gemini-3.6-flash"
# )

# model = ChatGoogleGenerativeAI(
#     model=RAG_MODEL,
#     temperature=0,
#     max_retries=2,
#     google_api_key=GOOGLE_API_KEY
# )

# print(
#     "✅ RAG Gemini models:",
#     MODEL_LIST_STR
# )

# ============================================================
# GEMINI EMBEDDINGS
# ============================================================

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview"
)


# ============================================================
# CHROMA VECTOR STORE
# ============================================================

vectorstore = Chroma(
    collection_name="my_collection",
    persist_directory="chroma_db",
    embedding_function=embeddings
)


# ============================================================
# DOCUMENT EMBEDDING
# ============================================================

def embed_documents_to_vectorstore(docs):
    """
    Split documents into chunks and store their
    Gemini embeddings inside Chroma.
    """

    if not docs:
        print("No documents to embed.")
        return


    # --------------------------------------------------------
    # TEXT SPLITTER
    # --------------------------------------------------------

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )


    # --------------------------------------------------------
    # CREATE CHUNKS
    # --------------------------------------------------------

    splits = text_splitter.split_documents(docs)

    print(
        f"Created {len(splits)} document chunks."
    )


    # --------------------------------------------------------
    # ADD TO CHROMA
    # --------------------------------------------------------

    if splits:

        vectorstore.add_documents(splits)

        print(
            "Documents embedded and saved to vectorstore."
        )

        print(
            "Total documents:",
            len(vectorstore.get()["documents"])
        )


# ============================================================
# RAG PROMPT
# ============================================================

system_prompt = (
    "You are an assistant for summarizing and answering "
    "queries from internal company documents.\n"

    "Always use the retrieved context to answer the query, "
    "even if partial.\n"

    "Do not guess. If data is not found, explain what "
    "you searched for.\n"

    "When responding:\n"

    "- Add **Source** from document metadata if possible.\n"
    "- Use headers.\n"
    "- Use bullet points.\n"
    "- For CSV-style data, format in a table with two columns.\n"

    "\n"
    "Retrieved Context:\n"
    "{context}"
)


chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_prompt
        ),
        (
            "human",
            "{input}"
        ),
    ]
)


# ============================================================
# ROLE-BASED RETRIEVER
# ============================================================

def get_rag_chain(user_role: str):

    user_role = user_role.lower()


    # --------------------------------------------------------
    # C-LEVEL
    # --------------------------------------------------------

    if user_role == "c-level":

        # C-Level can retrieve everything

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4
            }
        )


    # --------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------

    elif user_role == "general":

        # General users can only retrieve
        # General documents

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": {
                    "role": "general"
                }
            }
        )


    # --------------------------------------------------------
    # OTHER ROLES
    # --------------------------------------------------------

    else:

        # Other users can access:
        #
        # 1. Their own role documents
        # 2. General documents

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": {
                    "role": {
                        "$in": [
                            user_role,
                            "general"
                        ]
                    }
                }
            }
        )


    return retriever


# ============================================================
# GENERATE ANSWER
# ============================================================

# ============================================================
# GENERATE ANSWER
# ============================================================
# def generate_answer(question, documents):
#     """
#     Generate the final answer using the retrieved documents.
#     """

#     context = "\n\n---\n\n".join(
#         doc.page_content
#         for doc in documents
#     )

#     messages = chat_prompt.format_messages(
#         input=question,
#         context=context
#     )

#     try:
#         print(f"🤖 RAG model: {RAG_MODEL}")

#         response = model.invoke(messages)

#         if not response or not response.content:
#             raise RuntimeError("RAG model returned an empty response.")

#         content = response.content

#         if isinstance(content, str):
#             return content.strip()

#         if isinstance(content, list):
#             return "".join(
#                 item.get("text", "")
#                 for item in content
#                 if isinstance(item, dict)
#             ).strip()

#         return str(content).strip()

#     except Exception as e:
#         raise RuntimeError(
#             f"RAG generation failed using {RAG_MODEL}: {e}"
#         )
def generate_answer(question, documents):
    if not documents:
        return "I don't have enough information in the retrieved documents to answer this."
    context = "\n\n---\n\n".join(doc.page_content for doc in documents)
    messages = chat_prompt.format_messages(input=question, context=context)
    last_error = None
    for model_instance in RAG_MODELS:
        try:
            model_name = getattr(model_instance, "model_name", "unknown")
            print(f"🤖 RAG model: {model_name}")
            response = model_instance.invoke(messages)
            if not response:
                raise RuntimeError("LLM returned empty response.")
            content = response.content
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                text = "".join(item.get("text", "") for item in content if isinstance(item, dict))
                if text.strip():
                    return text.strip()
            return str(content).strip()
        except Exception as e:
            last_error = e
            print(f"⚠️ RAG model failed: {e}")
            print("🔄 Trying RAG fallback model...")
    raise RuntimeError(f"All RAG models failed. Last error: {last_error}")
# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(question: str, user_role: str):

    # --------------------------------------------------------
    # GET ROLE-BASED RETRIEVER
    # --------------------------------------------------------

    retriever = get_rag_chain(user_role)


    # --------------------------------------------------------
    # RETRIEVE DOCUMENTS
    # --------------------------------------------------------

    documents = retriever.invoke(question)


    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not documents:

        return {
            "answer": "I could not find relevant information.",
            "sources": []
        }


    # --------------------------------------------------------
    # GENERATE ANSWER
    # --------------------------------------------------------

    answer = generate_answer(
        question,
        documents
    )


    # --------------------------------------------------------
    # COLLECT SOURCES
    # --------------------------------------------------------

    sources = []

    for doc in documents:

        source = doc.metadata.get(
            "source"
        )

        if source and source not in sources:

            sources.append(source)


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "answer": answer,
        "sources": sources
    }