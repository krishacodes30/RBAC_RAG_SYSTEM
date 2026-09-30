# # app/evaluation/evaluate_rag.py

# import json
# import time
# import pandas as pd

# from app.rag_utils.rag_module import (
#     vectorstore,
#     get_rag_chain,
#     generate_answer
# )
# from app.llm.llm_provider import EVALUATOR_MODELS, EVALUATOR_MODEL
# from pathlib import Path

# # Folder where evaluator.py is located.
# EVALUATOR_DIR = Path(__file__).resolve().parent


# # ============================================================
# # ENVIRONMENT CONFIGURATION
# # ============================================================

# # ============================================================
# # EVALUATOR
# # ============================================================

# # This configured model acts as the evaluator/judge.
# # It evaluates the answers produced by our RAG system.
# evaluator_llm = EVALUATOR_MODELS
# # MODEL_LIST_STR = os.getenv(
# #     "FREE_GEMINI_MODELS",
# #     "gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash-lite"
# # )
# # evaluator_llm = [
# #     ChatGoogleGenerativeAI(
# #         model=model_name.strip(),
# #         temperature=0,
# #         max_retries=2,
# #         google_api_key=os.getenv("GOOGLE_API_KEY")
# #     )
# #     for model_name in MODEL_LIST_STR.split(",")
# #     if model_name.strip()
# # ]


# # ============================================================
# # GENERATE QUESTION FROM DOCUMENT CHUNK
# # ============================================================

# # def generate_question_with_gemini(text_chunk: str) -> str:
# #     """
# #     Generate one factual question from a document chunk.

# #     The question must be answerable directly from
# #     the supplied document content.
# #     """

# #     prompt = f"""
# # You are generating an evaluation question for a
# # Retrieval-Augmented Generation system.

# # Read this document chunk:

# # \"\"\"
# # {text_chunk}
# # \"\"\"

# # Create ONE specific factual question that can be
# # answered directly from this text.

# # Rules:
# # - The question must be answerable using only this text.
# # - Do not require outside knowledge.
# # - Do not ask an opinion question.
# # - Do not ask multiple questions.
# # - Return ONLY the question.
# # """

# #     # Send the prompt to Gemini.
# #     response = evaluator_llm.invoke(prompt)

# #     # Extract Gemini's text response.
# #     return response.content.strip()

# def generate_question_with_gemini(text_chunk: str) -> str:

#     prompt = f"""
# You are generating an evaluation question for a
# Retrieval-Augmented Generation system.

# Read this document chunk:

# {text_chunk}

# Create ONE specific factual question that can be
# answered directly from this text.

# Rules:
# - The question must be answerable using only this text.
# - Do not require outside knowledge.
# - Do not ask an opinion question.
# - Do not ask multiple questions.
# - Return ONLY the question.
# """

#     try:
#         print(f"🤖 Question generation: {EVALUATOR_MODEL}")

#         response = None
#         for model_instance in evaluator_llm:
#             try:
#                 response = model_instance.invoke(prompt)
#                 if response and response.content:
#                     break
#             except Exception:
#                 continue

#         if not response or not response.content:
#             raise RuntimeError("All evaluator models failed to respond.")

#         if isinstance(response.content, str):
#             return response.content.strip()

#         if isinstance(response.content, list):
#             return response.content[0]["text"].strip()

#         return str(response.content).strip()

#     except Exception as e:
#         raise RuntimeError(
#             f"Question generation failed: {e}"
#         )
# # ============================================================
# # GENERATE SYNTHETIC QA DATASET
# # ============================================================

# def generate_qa_dataset(
#     docs,
#     output_csv="qa_pairs_gemini.csv"
# ):
#     """
#     Generate evaluation questions from document chunks.

#     Each record contains:
#     - question
#     - answer/reference
#     - role
#     - source
#     """

#     qa_list = []

#     # Process every retrieved document chunk.
#     for index, doc in enumerate(docs):

#         print(
#             f"Generating question "
#             f"{index + 1}/{len(docs)}"
#         )

#         # Ask Gemini to create a question
#         # from this document chunk.
#         question = generate_question_with_gemini(
#             doc.page_content
#         )

#         # Store the question and the original chunk.
#         # The original chunk acts as the reference answer.
#         qa_list.append({
#             "question": question,
#             "answer": doc.page_content,
#             "role": doc.metadata.get("role", ""),
#             "source": doc.metadata.get("source", "")
#         })

#         # Small delay to avoid sending requests too quickly.
#         time.sleep(1)

#     # Convert the list into a DataFrame.
#     qa_df = pd.DataFrame(qa_list)

#     # Save the generated evaluation dataset.
#     qa_df.to_csv(
#         output_csv,
#         index=False
#     )

#     print(
#         f"\nQA dataset saved to: {output_csv}"
#     )

#     return qa_list


# # ============================================================
# # GEMINI RAG EVALUATOR
# # ============================================================

# # def evaluate_with_gemini(
# #     question: str,
# #     predicted_answer: str,
# #     retrieved_contexts: str,
# #     reference_answer: str
# # ) -> str:
# #     """
# #     Ask Gemini to evaluate one RAG response.

# #     Metrics:
# #     - faithfulness
# #     - relevancy
# #     - context_recall
# #     """

# #     prompt = f"""
# # You are an evaluator for a Retrieval-Augmented Generation system.

# # Evaluate the predicted answer using the question,
# # retrieved context, and reference answer.

# # Give a score between 0 and 1 for each metric.

# # METRICS:

# # 1. Faithfulness:
# # Is the predicted answer supported by the retrieved context?
# # Do not give credit for unsupported information.

# # 2. Relevancy:
# # Does the predicted answer directly answer the question?

# # 3. Context Recall:
# # Does the retrieved context contain the information
# # needed to answer the question according to the
# # reference answer?

# # QUESTION:
# # {question}

# # RETRIEVED CONTEXT:
# # {retrieved_contexts}

# # PREDICTED ANSWER:
# # {predicted_answer}

# # REFERENCE ANSWER:
# # {reference_answer}

# # Return ONLY valid JSON.

# # Required format:

# # {{
# #     "faithfulness": 0.0,
# #     "relevancy": 0.0,
# #     "context_recall": 0.0
# # }}
# # """

# #     # # Ask Gemini to evaluate the response.
# #     # response = evaluator_llm.invoke(prompt)

# #     # return response.content.strip()

# #     last_error = None

# #     # Try each Gemini evaluator model.
# #     for model in evaluator_llm:
# #         try:
# #             print(f"🤖 Evaluation model trying: {model.model}")

# #             response = model.invoke(prompt)

# #             if response and response.content:

# #                 content = response.content

# #                 if isinstance(content, str):
# #                     print(f"✅ Evaluation succeeded: {model.model}")
# #                     return content.strip()

# #                 if isinstance(content, list):
# #                     print(f"✅ Evaluation succeeded: {model.model}")
# #                     return content[0]["text"].strip()

# #         except Exception as e:
# #             last_error = e
# #             print(f"⚠️ Evaluation model failed ({model.model}): {e}")
# #             print("🔄 Trying next evaluation model...")

# #     raise RuntimeError(
# #         f"All Gemini evaluator models failed. Last error: {last_error}"
# #     )

# def evaluate_with_gemini(
#     question: str,
#     predicted_answer: str,
#     retrieved_contexts: str,
#     reference_answer: str
# ) -> str:
#     """
#     Ask Gemini to evaluate one RAG response.

#     Metrics:
#     - faithfulness
#     - relevancy
#     - context_recall
#     """

#     prompt = f"""
# You are a strict evaluator for a Retrieval-Augmented Generation system.

# Evaluate the predicted answer using ONLY the supplied information.

# QUESTION:
# {question}

# RETRIEVED CONTEXT:
# {retrieved_contexts}

# PREDICTED ANSWER:
# {predicted_answer}

# REFERENCE ANSWER:
# {reference_answer}

# Evaluate these three metrics independently.

# 1. Faithfulness:
# Does the predicted answer contain claims supported by the retrieved context?

# Scoring:
# 1.0 = All important claims are supported.
# 0.75 = Mostly supported, with minor unsupported details.
# 0.50 = Some important claims are unsupported.
# 0.25 = Most claims are unsupported.
# 0.0 = Answer is unsupported or contradicts the context.

# 2. Relevancy:
# Does the predicted answer directly answer the question?

# Scoring:
# 1.0 = Directly answers the question.
# 0.75 = Mostly answers the question.
# 0.50 = Partially answers the question.
# 0.25 = Barely addresses the question.
# 0.0 = Does not answer the question.

# 3. Context Recall:
# Does the retrieved context contain the information needed
# to answer the question according to the reference answer?

# Scoring:
# 1.0 = All important information is present.
# 0.75 = Most important information is present.
# 0.50 = Some important information is present.
# 0.25 = Very little information is present.
# 0.0 = Required information is absent.

# IMPORTANT:
# - Evaluate each metric independently.
# - Do NOT automatically give 1.0.
# - Give partial scores when appropriate.
# - Do not use outside knowledge.
# - Return ONLY valid JSON.

# Return exactly:

# {{
#     "faithfulness": 0.0,
#     "relevancy": 0.0,
#     "context_recall": 0.0
# }}
# """

#     try:
#         print(f"🤖 Evaluation model: {EVALUATOR_MODEL}")

#         response = None
#         last_error = None
#         for model_instance in evaluator_llm:
#             try:
#                 response = model_instance.invoke(prompt)
#                 if response and response.content:
#                     break
#             except Exception as error:
#                 last_error = error

#         if not response or not response.content:
#             raise RuntimeError(
#                 f"All evaluator models failed to respond: {last_error}"
#             )

#         if not response or not response.content:
#             raise RuntimeError("Evaluator returned an empty response.")

#         content = response.content

#         if isinstance(content, str):
#             return content.strip()

#         if isinstance(content, list):
#             return content[0]["text"].strip()

#         return str(content).strip()

#     except Exception as e:
#         raise RuntimeError(
#             f"RAG evaluation failed using {EVALUATOR_MODEL}: {e}"
#         )
# # ============================================================
# # CLEAN GEMINI JSON RESPONSE
# # ============================================================

# def clean_json_response(text: str) -> str:
#     """
#     Remove Markdown code fences if Gemini returns:

#     ```json
#     {...}
#     ```
#     """

#     text = text.strip()

#     # Remove opening JSON code fence.
#     if text.startswith("```json"):
#         text = text[7:]

#     # Remove generic opening code fence.
#     elif text.startswith("```"):
#         text = text[3:]

#     # Remove closing code fence.
#     if text.endswith("```"):
#         text = text[:-3]

#     return text.strip()


# # ============================================================
# # RUN RAG EVALUATION
# # ============================================================

# def run_rag_eval(
#     qa_list,
#     retriever,
#     output_csv="evaluation_results_gemini.csv"
# ):
#     """
#     Run every generated question through the actual RAG system.

#     For every question we save:
#     - question
#     - prediction
#     - ground truth
#     - retrieved contexts
#     - role
#     - source
#     - evaluation metrics
#     """

#     # Create the actual RAG chain that we want to test.
#     # qa_chain = RetrievalQA.from_chain_type(
#     #     llm=model,
#     #     retriever=retriever,
#     #     return_source_documents=True
#     # )

#     results = []

#     # Evaluate every question.
#     for index, qa in enumerate(qa_list):

#         print(
#             f"\nEvaluating question "
#             f"{index + 1}/{len(qa_list)}"
#         )

#         question = qa["question"]

#         # Original document chunk used as reference.
#         ground_truth = qa["answer"]

#         # Get role and source from the generated QA dataset.
#         role = qa.get("role", "")
#         source = qa.get("source", "")

#         try:

#             source_documents = retriever.invoke(
#                 question
#             )
#             predicted = generate_answer(
#                 question,
#                 source_documents
#             )
#             contexts = "\n---\n".join(
#                 doc.page_content
#                 for doc in source_documents
#             )

#             # ------------------------------------------------
#             # ASK GEMINI TO EVALUATE THE RAG ANSWER
#             # ------------------------------------------------

#             raw_scores = evaluate_with_gemini(
#                 question=question,
#                 predicted_answer=predicted,
#                 retrieved_contexts=contexts,
#                 reference_answer=ground_truth
#             )

#             # Clean possible Markdown fences.
#             cleaned_scores = clean_json_response(
#                 raw_scores
#             )

#             # Convert JSON string into Python dictionary.
#             scores = json.loads(
#                 cleaned_scores
#             )

#         except Exception as e:

#             print(
#                 f"Evaluation failed: {e}"
#             )

#             # Keep the evaluation running even if
#             # one question fails.
#             predicted = ""
#             contexts = ""

#             scores = {
#                 "faithfulness": None,
#                 "relevancy": None,
#                 "context_recall": None,
#                 "error": str(e)
#             }

#         # ----------------------------------------------------
#         # SAVE THIS QUESTION'S COMPLETE RESULT
#         # ----------------------------------------------------

#         results.append({
#             "question": question,
#             "prediction": predicted,
#             "ground_truth": ground_truth,
#             "contexts": contexts,
#             "role": role,
#             "source": source,
#             "metrics": json.dumps(scores)
#         })

#         # Small delay between evaluation requests.
#         time.sleep(1)

#     # Convert all results into DataFrame.
#     results_df = pd.DataFrame(results)

#     # Save evaluation results.
#     results_df.to_csv(
#         output_csv,
#         index=False
#     )

#     print(
#         f"\nEvaluation results saved to: {output_csv}"
#     )

#     return results


# # ============================================================
# # MAIN EXECUTION
# # ============================================================

# # if __name__ == "__main__":

# #     # --------------------------------------------------------
# #     # STEP 1:
# #     # Retrieve many chunks to create evaluation questions.
# #     # --------------------------------------------------------

# #     docs = vectorstore.similarity_search(
# #         "finance",
# #         k=10
# #     )

# #     print(
# #         f"Retrieved {len(docs)} chunks "
# #         f"for evaluation dataset."
# #     )

# #     # --------------------------------------------------------
# #     # STEP 2:
# #     # Generate synthetic evaluation questions.
# #     # --------------------------------------------------------

# # #     qa_list = generate_qa_dataset(
# # #     docs,
# # #     output_csv=EVALUATOR_DIR / "qa_pairs_gemini.csv"
# # # )

# #     # --------------------------------------------------------
# #     # STEP 3:
# #     # Create the retriever used by the real RAG system.
# #     # --------------------------------------------------------

# #     retriever = vectorstore.as_retriever(
# #         search_kwargs={
# #             "k": 4
# #         }
# #     )

# #     # --------------------------------------------------------
# #     # STEP 4:
# #     # Run RAG evaluation.
# #     # --------------------------------------------------------

# #     run_rag_eval(
# #     qa_list,
# #     retriever,
# #     output_csv=EVALUATOR_DIR / "evaluation_results_gemini.csv"
# # )

# #     print("\nRAG evaluation completed successfully.")



# if __name__ == "__main__":

#     # ========================================================
#     # CONFIGURATION
#     # ========================================================

#     # False = use existing QA dataset
#     # True  = generate a new QA dataset first
#     GENERATE_NEW_QA = True

#     QA_FILE = EVALUATOR_DIR / "qa_pairs_gemini.csv"
#     EVALUATION_FILE = EVALUATOR_DIR / "evaluation_results_gemini.csv"


#     # ========================================================
#     # STEP 1: QA DATASET
#     # ========================================================

#     if GENERATE_NEW_QA:

#         print("\n🆕 Generating new QA dataset...")

#         # Retrieve chunks from your vector database
#         docs = vectorstore.similarity_search(
#             "finance",
#             k=10
#         )

#         print(
#             f"📚 Retrieved {len(docs)} chunks "
#             f"for QA generation."
#         )

#         # Generate QA dataset
#         qa_list = generate_qa_dataset(
#             docs,
#             output_csv=QA_FILE
#         )

#         print(
#             f"✅ Generated {len(qa_list)} QA pairs."
#         )

#     else:

#         # ====================================================
#         # USE EXISTING QA DATASET
#         # ====================================================

#         if not QA_FILE.exists():
#             raise FileNotFoundError(
#                 f"""
# QA dataset not found:

# {QA_FILE}

# Set:

# GENERATE_NEW_QA = True

# to generate it first.
# """
#             )

#         print(
#             f"\n📂 Loading existing QA dataset:\n"
#             f"{QA_FILE}"
#         )

#         qa_df = pd.read_csv(QA_FILE)
#         qa_df = qa_df.head(20)

#         qa_list = qa_df.to_dict(
#             orient="records"
#         )
        

#         print(
#             f"✅ Loaded {len(qa_list)} "
#             f"existing evaluation questions."
#         )


#     # ========================================================
#     # STEP 2: CREATE RAG RETRIEVER
#     # ========================================================

#     print("\n🔎 Creating RAG retriever...")
#     retriever = get_rag_chain(role)

#     # retriever = vectorstore.as_retriever(
#     #     search_kwargs={
#     #         "k": 4
#     #     }
#     # )


#     # ========================================================
#     # STEP 3: RUN EVALUATION
#     # ========================================================

#     print("\n🚀 Starting RAG evaluation...")

#     run_rag_eval(
#         qa_list,
#         retriever,
#         output_csv=EVALUATION_FILE
#     )

#     print(
#         "\n✅ RAG evaluation completed successfully."
#     )


import json
import time
import pandas as pd
from pathlib import Path
from langchain_core.documents import Document

from app.rag_utils.rag_module import (
    vectorstore,
    get_rag_chain,
    generate_answer
)
from app.llm.llm_provider import EVALUATOR_MODELS, EVALUATOR_MODEL

EVALUATOR_DIR = Path(__file__).resolve().parent

# =========================
# EVALUATION CONFIGURATION
# =========================

QA_MODE = "generate"          # "generate" or "existing"
NUM_QA_QUESTIONS = 30        # number of questions to evaluate
RETRIEVAL_K = 4               # top-k chunks retrieved per question

GENERATE_QUESTIONS_WITH_GEMINI = True
BALANCE_QA_BY_ROLE = True

QUESTION_DELAY = 1            # delay after question generation
EVALUATION_DELAY = 1          # delay after evaluation

QA_FILE = EVALUATOR_DIR / "qa_pairs_gemini.csv"
EVALUATION_FILE = EVALUATOR_DIR / "evaluation_results_gemini.csv"

# =========================
# MODEL HELPERS
# =========================

def get_model_list():
    if isinstance(EVALUATOR_MODELS, (list, tuple)):
        return list(EVALUATOR_MODELS)
    return [EVALUATOR_MODELS]

def get_model_name(model_instance):
    return getattr(
        model_instance,
        "model_name",
        getattr(model_instance, "model", "unknown")
    )

def invoke_evaluator(prompt):
    last_error = None

    for model_instance in get_model_list():
        model_name = get_model_name(model_instance)

        try:
            print(f"🤖 Model: {model_name}")

            response = model_instance.invoke(prompt)

            if response and response.content:
                content = response.content

                if isinstance(content, str):
                    return content.strip(), model_name

                if isinstance(content, list):
                    text = "".join(
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict)
                    ).strip()

                    if text:
                        return text, model_name

                return str(content).strip(), model_name

        except Exception as error:
            last_error = error
            print(f"⚠️ {model_name} failed: {error}")
            print("🔄 Trying next evaluator model...")

    raise RuntimeError(
        f"All evaluator models failed. Last error: {last_error}"
    )

# =========================
# QUESTION GENERATION
# =========================

def generate_question_with_gemini(text_chunk):
    prompt = f"""
You are generating an evaluation question for a Retrieval-Augmented Generation system.

DOCUMENT:
{text_chunk}

Create ONE specific factual question that can be answered directly from the document.

Rules:
- Use only the supplied document.
- Do not use outside knowledge.
- Do not ask an opinion question.
- Do not ask multiple questions.
- The question must have a clear factual answer.
- Return ONLY the question.
"""

    try:
        question, model_name = invoke_evaluator(prompt)

        question = question.strip()

        if question.startswith("```"):
            question = question.replace("```", "").strip()

        if not question:
            raise RuntimeError("Gemini returned an empty question.")

        print(f"✅ Question generated using {model_name}")

        return question

    except Exception as error:
        raise RuntimeError(
            f"Question generation failed: {error}"
        )

# =========================
# GET DOCUMENTS FOR QA
# =========================

def get_source_documents(limit):
    data = vectorstore.get(
        include=["documents", "metadatas"]
    )

    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])

    source_docs = []

    for index, content in enumerate(documents):
        if not content:
            continue

        metadata = {}

        if index < len(metadatas) and metadatas[index]:
            metadata = metadatas[index]

        source_docs.append(
            Document(
                page_content=content,
                metadata=metadata
            )
        )

    if not source_docs:
        raise RuntimeError(
            "No documents found in the vector store."
        )

    if not BALANCE_QA_BY_ROLE:
        return source_docs[:limit]

    # Select documents in a round-robin manner by role.
    role_groups = {}

    for doc in source_docs:
        role = str(
            doc.metadata.get("role", "general")
        ).lower()

        role_groups.setdefault(
            role,
            []
        ).append(doc)

    selected = []

    while len(selected) < limit:
        added = False

        for role_docs in role_groups.values():
            if not role_docs:
                continue

            selected.append(
                role_docs.pop(0)
            )

            added = True

            if len(selected) >= limit:
                break

        if not added:
            break

    return selected

# =========================
# GENERATE QA DATASET
# =========================

def generate_qa_dataset(
    docs,
    output_csv=QA_FILE
):
    qa_list = []
    used_questions = set()

    for index, doc in enumerate(docs):
        print(
            f"\nGenerating question "
            f"{index + 1}/{len(docs)}"
        )

        try:
            question = generate_question_with_gemini(
                doc.page_content
            )

            normalized_question = question.lower().strip()

            if normalized_question in used_questions:
                print("⚠️ Duplicate question skipped.")
                continue

            used_questions.add(
                normalized_question
            )

            role = str(
                doc.metadata.get(
                    "role",
                    "general"
                )
            ).strip().lower()

            source = doc.metadata.get(
                "source",
                ""
            )

            qa_list.append({
                "question": question,
                "answer": doc.page_content,
                "role": role,
                "source": source
            })

            time.sleep(QUESTION_DELAY)

        except Exception as error:
            print(
                f"⚠️ Question generation failed: {error}"
            )

    if not qa_list:
        raise RuntimeError(
            "No QA questions were generated."
        )

    qa_df = pd.DataFrame(qa_list)

    qa_df.to_csv(
        output_csv,
        index=False
    )

    print(
        f"\n✅ QA dataset saved to: {output_csv}"
    )

    print(
        f"✅ Generated questions: {len(qa_list)}"
    )

    return qa_list

# =========================
# EVALUATION PROMPT
# =========================

def evaluate_with_gemini(
    question,
    predicted_answer,
    retrieved_contexts,
    reference_answer
):
    prompt = f"""
You are a strict evaluator for a Retrieval-Augmented Generation system.

Evaluate the predicted answer using ONLY the supplied information.

QUESTION:
{question}

RETRIEVED CONTEXT:
{retrieved_contexts}

PREDICTED ANSWER:
{predicted_answer}

REFERENCE ANSWER:
{reference_answer}

Evaluate these three metrics independently.

1. Faithfulness:
Does the predicted answer contain claims supported by the retrieved context?

1.0 = All important claims are supported.
0.75 = Mostly supported with minor unsupported details.
0.50 = Some important claims are unsupported.
0.25 = Most claims are unsupported.
0.0 = Unsupported or contradicts the context.

2. Relevancy:
Does the predicted answer directly answer the question?

1.0 = Directly answers the question.
0.75 = Mostly answers the question.
0.50 = Partially answers the question.
0.25 = Barely addresses the question.
0.0 = Does not answer the question.

3. Context Recall:
Does the retrieved context contain the information needed to answer the question according to the reference answer?

1.0 = All important information is present.
0.75 = Most important information is present.
0.50 = Some important information is present.
0.25 = Very little information is present.
0.0 = Required information is absent.

IMPORTANT:
- Evaluate every metric independently.
- Do not automatically give 1.0.
- Use partial scores when appropriate.
- Do not use outside knowledge.
- Return ONLY valid JSON.

Return exactly:

{{
    "faithfulness": 0.0,
    "relevancy": 0.0,
    "context_recall": 0.0
}}
"""

    content, model_name = invoke_evaluator(
        prompt
    )

    return content, model_name

# =========================
# JSON / SCORE VALIDATION
# =========================

def clean_json_response(text):
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text

def validate_scores(scores):
    required = [
        "faithfulness",
        "relevancy",
        "context_recall"
    ]

    for metric in required:
        if metric not in scores:
            raise ValueError(
                f"Missing metric: {metric}"
            )

        value = scores[metric]

        if not isinstance(
            value,
            (int, float)
        ):
            raise ValueError(
                f"{metric} must be numeric."
            )

        if not 0 <= value <= 1:
            raise ValueError(
                f"{metric} must be between 0 and 1."
            )

    return {
        "faithfulness": float(
            scores["faithfulness"]
        ),
        "relevancy": float(
            scores["relevancy"]
        ),
        "context_recall": float(
            scores["context_recall"]
        )
    }

# =========================
# RBAC VALIDATION
# =========================

def check_rbac_access(user_role, documents):
    user_role = str(
        user_role or "general"
    ).lower()

    retrieved_roles = []

    for doc in documents:
        role = str(
            doc.metadata.get(
                "role",
                "general"
            )
        ).lower()

        retrieved_roles.append(role)

    if user_role == "c-level":
        return retrieved_roles, False

    allowed_roles = {
        user_role,
        "general"
    }

    violation = any(
        role not in allowed_roles
        for role in retrieved_roles
    )

    return retrieved_roles, violation

# =========================
# RUN RAG EVALUATION
# =========================

def run_rag_eval(
    qa_list,
    output_csv=EVALUATION_FILE
):
    results = []
    successful = 0
    failed = 0

    for index, qa in enumerate(qa_list):
        question = str(
            qa.get("question", "")
        ).strip()

        ground_truth = str(
            qa.get("answer", "")
        )

        role = str(
            qa.get("role", "general")
        ).strip().lower()

        expected_source = qa.get(
            "source",
            ""
        )

        print(
            f"\n{'=' * 60}\n"
            f"Evaluating {index + 1}/{len(qa_list)}\n"
            f"Role: {role}\n"
            f"Question: {question}\n"
            f"{'=' * 60}"
        )

        predicted = ""
        contexts = ""
        retrieved_sources = []
        retrieved_roles = []
        scores = {
            "faithfulness": None,
            "relevancy": None,
            "context_recall": None
        }
        evaluator_model = ""
        error_message = ""
        rbac_violation = False

        try:
            # IMPORTANT:
            # Role is taken from the current QA row.
            # This makes evaluation use the same RBAC
            # retrieval policy as the application.
            retriever = get_rag_chain(role)

            # Override k without removing the role filter.
            if hasattr(
                retriever,
                "search_kwargs"
            ):
                retriever.search_kwargs["k"] = RETRIEVAL_K

            source_documents = retriever.invoke(
                question
            )

            retrieved_sources = list(
                dict.fromkeys(
                    doc.metadata.get(
                        "source",
                        ""
                    )
                    for doc in source_documents
                    if doc.metadata.get(
                        "source",
                        ""
                    )
                )
            )

            retrieved_roles, rbac_violation = (
                check_rbac_access(
                    role,
                    source_documents
                )
            )

            contexts = "\n---\n".join(
                doc.page_content
                for doc in source_documents
            )

            predicted = generate_answer(
                question,
                source_documents
            )

            raw_scores, evaluator_model = (
                evaluate_with_gemini(
                    question=question,
                    predicted_answer=predicted,
                    retrieved_contexts=contexts,
                    reference_answer=ground_truth
                )
            )

            cleaned_scores = clean_json_response(
                raw_scores
            )

            scores = validate_scores(
                json.loads(cleaned_scores)
            )

            successful += 1

            print(
                f"✅ Faithfulness: "
                f"{scores['faithfulness']:.2f}"
            )
            print(
                f"✅ Relevancy: "
                f"{scores['relevancy']:.2f}"
            )
            print(
                f"✅ Context Recall: "
                f"{scores['context_recall']:.2f}"
            )

            if rbac_violation:
                print(
                    "🚨 RBAC VIOLATION DETECTED"
                )

        except Exception as error:
            failed += 1
            error_message = str(error)

            print(
                f"❌ Evaluation failed: "
                f"{error_message}"
            )

        results.append({
            "question": question,
            "prediction": predicted,
            "ground_truth": ground_truth,
            "contexts": contexts,
            "role": role,
            "expected_source": expected_source,
            "retrieved_sources": json.dumps(
                retrieved_sources
            ),
            "retrieved_roles": json.dumps(
                retrieved_roles
            ),
            "rbac_violation": rbac_violation,
            "evaluator_model": evaluator_model,
            "faithfulness": scores[
                "faithfulness"
            ],
            "relevancy": scores[
                "relevancy"
            ],
            "context_recall": scores[
                "context_recall"
            ],
            "metrics": json.dumps(
                scores
            ),
            "error": error_message
        })

        time.sleep(
            EVALUATION_DELAY
        )

    results_df = pd.DataFrame(
        results
    )

    results_df.to_csv(
        output_csv,
        index=False
    )

    print("\n" + "=" * 60)
    print("RAG EVALUATION SUMMARY")
    print("=" * 60)
    print(
        f"Total questions     : {len(qa_list)}"
    )
    print(
        f"Successful          : {successful}"
    )
    print(
        f"Failed              : {failed}"
    )
    print(
        f"Retrieval k         : {RETRIEVAL_K}"
    )
    print(
        f"Results saved to    : {output_csv}"
    )
    print("=" * 60)

    return results

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RAG EVALUATION")
    print("=" * 60)
    print(
        f"QA mode             : {QA_MODE}"
    )
    print(
        f"Questions           : {NUM_QA_QUESTIONS}"
    )
    print(
        f"Retrieval k         : {RETRIEVAL_K}"
    )
    print(
        f"Gemini QA generation: "
        f"{GENERATE_QUESTIONS_WITH_GEMINI}"
    )
    print("=" * 60)

    if QA_MODE == "generate":
        if not GENERATE_QUESTIONS_WITH_GEMINI:
            raise ValueError(
                "QA_MODE='generate' requires "
                "GENERATE_QUESTIONS_WITH_GEMINI=True."
            )

        docs = get_source_documents(
            NUM_QA_QUESTIONS
        )

        print(
            f"\n📚 Selected {len(docs)} "
            f"document chunks for QA generation."
        )

        qa_list = generate_qa_dataset(
            docs,
            output_csv=QA_FILE
        )

        # Keep the configured maximum.
        qa_list = qa_list[
            :NUM_QA_QUESTIONS
        ]

    elif QA_MODE == "existing":
        if not QA_FILE.exists():
            raise FileNotFoundError(
                f"QA dataset not found:\n{QA_FILE}"
            )

        print(
            f"\n📂 Loading existing QA dataset:\n"
            f"{QA_FILE}"
        )

        qa_df = pd.read_csv(
            QA_FILE
        )

        qa_df = qa_df.head(
            NUM_QA_QUESTIONS
        )

        qa_list = qa_df.to_dict(
            orient="records"
        )

        print(
            f"✅ Loaded {len(qa_list)} "
            f"questions."
        )

    else:
        raise ValueError(
            "QA_MODE must be "
            "'generate' or 'existing'."
        )

    if not qa_list:
        raise RuntimeError(
            "No evaluation questions available."
        )

    run_rag_eval(
        qa_list,
        output_csv=EVALUATION_FILE
    )

    print("\n✅ RAG evaluation completed successfully.")
