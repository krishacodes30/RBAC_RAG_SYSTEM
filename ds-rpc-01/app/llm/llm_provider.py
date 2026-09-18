import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PROVIDER
# ============================================================
#
# Change ONLY this:
#
LLM_PROVIDER="groq"
#
# or'
#
# LLM_PROVIDER=gemini
#
# Nothing else in your application needs to change.
# ============================================================

# LLM_PROVIDER = os.getenv(
#     "LLM_PROVIDER",
#     "groq"
# ).strip().lower()


# ============================================================
# API KEYS
# ============================================================

GOOGLE_API_KEY = os.getenv(
    "GOOGLE_API_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


# ============================================================
# MODEL NAMES
# ============================================================
#
# IMPORTANT:
# Keep different names for different purposes.
#
# RAG_MODEL       -> final RAG answer
# SQL_MODEL       -> natural language -> SQL
# CLASSIFIER_MODEL -> SQL/RAG classification
# EVALUATOR_MODEL -> RAG evaluation
#
# You can change these independently.
# ============================================================

RAG_MODEL = os.getenv(
    "RAG_MODEL",
    "openai/gpt-oss-120b"
)

RAG_FALLBACK_MODEL = os.getenv(
    "RAG_FALLBACK_MODEL",
    "openai/gpt-oss-20b"
)


SQL_MODEL = os.getenv(
    "SQL_MODEL",
    "openai/gpt-oss-120b"
)

SQL_FALLBACK_MODEL = os.getenv(
    "SQL_FALLBACK_MODEL",
    "openai/gpt-oss-20b"
)


CLASSIFIER_MODEL = os.getenv(
    "CLASSIFIER_MODEL",
    "openai/gpt-oss-20b"
)

CLASSIFIER_FALLBACK_MODEL = os.getenv(
    "CLASSIFIER_FALLBACK_MODEL",
    "openai/gpt-oss-20b"
)


EVALUATOR_MODEL = os.getenv(
    "EVALUATOR_MODEL",
    "openai/gpt-oss-120b"
)

EVALUATOR_FALLBACK_MODEL = os.getenv(
    "EVALUATOR_FALLBACK_MODEL",
    "openai/gpt-oss-20b"
)


# ============================================================
# MODEL FACTORY
# ============================================================

def create_llm(
    model_name: str,
    temperature: float = 0,
    max_tokens: int = 2048
):
    """
    Create an LLM according to the centralized provider.

    Change LLM_PROVIDER in .env:
        groq
        gemini
    """

    if LLM_PROVIDER == "groq":

        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing from .env"
            )

        return ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=2,
            groq_api_key=GROQ_API_KEY
        )


    elif LLM_PROVIDER == "gemini":

        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is missing from .env"
            )

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
            max_retries=2,
            google_api_key=GOOGLE_API_KEY
        )


    else:

        raise ValueError(
            f"Unsupported LLM_PROVIDER: "
            f"{LLM_PROVIDER}. "
            f"Use 'groq' or 'gemini'."
        )


# ============================================================
# FALLBACK MODEL FACTORY
# ============================================================

def create_model_list(
    primary_model: str,
    fallback_model: str,
    temperature: float = 0,
    max_tokens: int = 2048
):
    """
    Create primary + fallback LLMs.

    Example:

    [
        GPT-OSS-120B,
        GPT-OSS-20B
    ]
    """

    models = []

    # Primary
    models.append(
        create_llm(
            model_name=primary_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    )

    # Fallback
    if fallback_model:

        # Avoid creating duplicate model
        if fallback_model != primary_model:

            models.append(
                create_llm(
                    model_name=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            )

    return models


# ============================================================
# RAG
# ============================================================

RAG_MODELS = create_model_list(
    RAG_MODEL,
    RAG_FALLBACK_MODEL,
    temperature=0,
    max_tokens=2048
)


# ============================================================
# SQL
# ============================================================

SQL_MODELS = create_model_list(
    SQL_MODEL,
    SQL_FALLBACK_MODEL,
    temperature=0,
    max_tokens=2048
)


# ============================================================
# CLASSIFIER
# ============================================================

CLASSIFIER_MODELS = create_model_list(
    CLASSIFIER_MODEL,
    CLASSIFIER_FALLBACK_MODEL,
    temperature=0,
    max_tokens=512
)


# ============================================================
# EVALUATOR
# ============================================================

EVALUATOR_MODELS = create_model_list(
    EVALUATOR_MODEL,
    EVALUATOR_FALLBACK_MODEL,
    temperature=0,
    max_tokens=1000
)


# ============================================================
# BACKWARD-COMPATIBLE NAMES
# ============================================================
#
# These names intentionally match your existing files.
#
# Therefore you don't have to redesign your application.
# ============================================================

# RAG
model = RAG_MODELS[0]

# SQL
free_models = SQL_MODELS

# Classifier
classifier_model = CLASSIFIER_MODELS[0]

# Evaluator
evaluator_llm = EVALUATOR_MODELS