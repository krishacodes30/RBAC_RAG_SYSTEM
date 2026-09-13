# ========== CONFIG ==========
from pathlib import Path
import os
import pandas as pd
from collections import defaultdict
from langchain.schema import Document
import sqlite3


from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# from langchain_openai import OpenAIEmbeddings
# from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_st


from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing from .env")







def load_file(filepath, role):
    ext = Path(filepath).suffix.lower()
    try:
        if ext == ".csv":
            df1 = pd.read_csv(filepath)
            documents = []
            for row in df1.to_dict(orient="records"):
                content = "\n".join(f"{k}: {v}" for k, v in row.items())
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"role": role.lower(), "source": Path(filepath).name}
                    )
                )
            return documents  # Return a list of documents

        elif ext == ".md":
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return [
                Document(
                    page_content=content,
                    metadata={"role": role.lower(), "source": Path(filepath).name}
                )
            ]
        else:
            return None

    except Exception as e:
        print(f"Failed to process {filepath}: {e}")
        return None



from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
    max_retries=2,
    # other params...
)

from langchain_google_genai import GoogleGenerativeAIEmbeddings





# openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

vectorstore = Chroma(
    collection_name="my_collection",
    persist_directory="chroma_db",
    embedding_function=embeddings
)

def embed_documents_to_vectorstore(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    vectorstore.add_documents(splits)
    
    print("Documents embedded and saved to vectorstore.")
    print("Total documents:", len(vectorstore.get()["documents"]))
    #print("Chunks being added:")
    #for chunk in splits:
    #    print(f"---\n{chunk.page_content[:150]}...\nMetadata: {chunk.metadata}")


# ==============================
# ========== PROMPT TEMPLATE ==========
# ==============================
system_prompt = (
    "You are an assistant for summarizing and answering queries from internal company documents.\n"
    "Always use the retrieved context to answer the query, even if partial.\n"
    "Do not guess. If data is not found, explain what you searched for.\n"
    "When responding:\n"
    "- Add **Source** from document metadata if possible.\n"
    "- Use headers\n"
    "- Use bullet points\n"
    "- For CSV-style data, format in table with two columns\n"
    "\n{context}"
)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

from langchain.chains.combine_documents import create_stuff_documents_chain
question_answering_chain = create_stuff_documents_chain(model, chat_prompt)


def get_rag_chain(user_role: str,cohere_api_key: str = None):
    user_role = user_role.lower()

    if user_role == "c-level":
        # C-level sees everything
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    elif user_role == "general":
        # General role sees only general documents
        retriever = vectorstore.as_retriever(search_kwargs={
            "k": 4,
            "filter": {"role": "general"}
        })

    else:
        # All other roles see their docs + general
        retriever = vectorstore.as_retriever(search_kwargs={
            "k": 4,
            "filter": {
                "role": {"$in": [user_role, "general"]}
            }
        })

        return retriever, question_answering_chain


def ask_question(question: str, user_role: str):

      retriever, qa_chain = get_rag_chain(user_role)

      documents = retriever.invoke(question)

      if not documents:

        return {
            "answer": "I could not find relevant information.",
            "sources": []
        }

      response = qa_chain.invoke({
        "input": question,
        "context": documents
    })
      sources = []

      for doc in documents:

        source = doc.metadata.get("source")

        if source and source not in sources:
            sources.append(source)


    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

      return {
        "answer": response,
        "sources": sources
    }
      


