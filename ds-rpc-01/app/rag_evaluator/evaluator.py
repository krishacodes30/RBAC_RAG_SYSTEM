# app/evaluation/evaluate_rag.py

import json
import time
import pandas as pd

from app.rag_utils.rag_module import (
    vectorstore,
    get_rag_chain,
    generate_answer
)
from app.llm.llm_provider import EVALUATOR_MODELS, EVALUATOR_MODEL
from pathlib import Path

# Folder where evaluator.py is located.
EVALUATOR_DIR = Path(__file__).resolve().parent


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

# ============================================================
# EVALUATOR
# ============================================================

# This configured model acts as the evaluator/judge.
# It evaluates the answers produced by our RAG system.
evaluator_llm = EVALUATOR_MODELS
# MODEL_LIST_STR = os.getenv(
#     "FREE_GEMINI_MODELS",
#     "gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash-lite"
# )
# evaluator_llm = [
#     ChatGoogleGenerativeAI(
#         model=model_name.strip(),
#         temperature=0,
#         max_retries=2,
#         google_api_key=os.getenv("GOOGLE_API_KEY")
#     )
#     for model_name in MODEL_LIST_STR.split(",")
#     if model_name.strip()
# ]


# ============================================================
# GENERATE QUESTION FROM DOCUMENT CHUNK
# ============================================================

# def generate_question_with_gemini(text_chunk: str) -> str:
#     """
#     Generate one factual question from a document chunk.

#     The question must be answerable directly from
#     the supplied document content.
#     """

#     prompt = f"""
# You are generating an evaluation question for a
# Retrieval-Augmented Generation system.

# Read this document chunk:

# \"\"\"
# {text_chunk}
# \"\"\"

# Create ONE specific factual question that can be
# answered directly from this text.

# Rules:
# - The question must be answerable using only this text.
# - Do not require outside knowledge.
# - Do not ask an opinion question.
# - Do not ask multiple questions.
# - Return ONLY the question.
# """

#     # Send the prompt to Gemini.
#     response = evaluator_llm.invoke(prompt)

#     # Extract Gemini's text response.
#     return response.content.strip()

def generate_question_with_gemini(text_chunk: str) -> str:

    prompt = f"""
You are generating an evaluation question for a
Retrieval-Augmented Generation system.

Read this document chunk:

{text_chunk}

Create ONE specific factual question that can be
answered directly from this text.

Rules:
- The question must be answerable using only this text.
- Do not require outside knowledge.
- Do not ask an opinion question.
- Do not ask multiple questions.
- Return ONLY the question.
"""

    try:
        print(f"🤖 Question generation: {EVALUATOR_MODEL}")

        response = None
        for model_instance in evaluator_llm:
            try:
                response = model_instance.invoke(prompt)
                if response and response.content:
                    break
            except Exception:
                continue

        if not response or not response.content:
            raise RuntimeError("All evaluator models failed to respond.")

        if isinstance(response.content, str):
            return response.content.strip()

        if isinstance(response.content, list):
            return response.content[0]["text"].strip()

        return str(response.content).strip()

    except Exception as e:
        raise RuntimeError(
            f"Question generation failed: {e}"
        )
# ============================================================
# GENERATE SYNTHETIC QA DATASET
# ============================================================

def generate_qa_dataset(
    docs,
    output_csv="qa_pairs_gemini.csv"
):
    """
    Generate evaluation questions from document chunks.

    Each record contains:
    - question
    - answer/reference
    - role
    - source
    """

    qa_list = []

    # Process every retrieved document chunk.
    for index, doc in enumerate(docs):

        print(
            f"Generating question "
            f"{index + 1}/{len(docs)}"
        )

        # Ask Gemini to create a question
        # from this document chunk.
        question = generate_question_with_gemini(
            doc.page_content
        )

        # Store the question and the original chunk.
        # The original chunk acts as the reference answer.
        qa_list.append({
            "question": question,
            "answer": doc.page_content,
            "role": doc.metadata.get("role", ""),
            "source": doc.metadata.get("source", "")
        })

        # Small delay to avoid sending requests too quickly.
        time.sleep(1)

    # Convert the list into a DataFrame.
    qa_df = pd.DataFrame(qa_list)

    # Save the generated evaluation dataset.
    qa_df.to_csv(
        output_csv,
        index=False
    )

    print(
        f"\nQA dataset saved to: {output_csv}"
    )

    return qa_list


# ============================================================
# GEMINI RAG EVALUATOR
# ============================================================

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
# You are an evaluator for a Retrieval-Augmented Generation system.

# Evaluate the predicted answer using the question,
# retrieved context, and reference answer.

# Give a score between 0 and 1 for each metric.

# METRICS:

# 1. Faithfulness:
# Is the predicted answer supported by the retrieved context?
# Do not give credit for unsupported information.

# 2. Relevancy:
# Does the predicted answer directly answer the question?

# 3. Context Recall:
# Does the retrieved context contain the information
# needed to answer the question according to the
# reference answer?

# QUESTION:
# {question}

# RETRIEVED CONTEXT:
# {retrieved_contexts}

# PREDICTED ANSWER:
# {predicted_answer}

# REFERENCE ANSWER:
# {reference_answer}

# Return ONLY valid JSON.

# Required format:

# {{
#     "faithfulness": 0.0,
#     "relevancy": 0.0,
#     "context_recall": 0.0
# }}
# """

#     # # Ask Gemini to evaluate the response.
#     # response = evaluator_llm.invoke(prompt)

#     # return response.content.strip()

#     last_error = None

#     # Try each Gemini evaluator model.
#     for model in evaluator_llm:
#         try:
#             print(f"🤖 Evaluation model trying: {model.model}")

#             response = model.invoke(prompt)

#             if response and response.content:

#                 content = response.content

#                 if isinstance(content, str):
#                     print(f"✅ Evaluation succeeded: {model.model}")
#                     return content.strip()

#                 if isinstance(content, list):
#                     print(f"✅ Evaluation succeeded: {model.model}")
#                     return content[0]["text"].strip()

#         except Exception as e:
#             last_error = e
#             print(f"⚠️ Evaluation model failed ({model.model}): {e}")
#             print("🔄 Trying next evaluation model...")

#     raise RuntimeError(
#         f"All Gemini evaluator models failed. Last error: {last_error}"
#     )

def evaluate_with_gemini(
    question: str,
    predicted_answer: str,
    retrieved_contexts: str,
    reference_answer: str
) -> str:
    """
    Ask Gemini to evaluate one RAG response.

    Metrics:
    - faithfulness
    - relevancy
    - context_recall
    """

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

Scoring:
1.0 = All important claims are supported.
0.75 = Mostly supported, with minor unsupported details.
0.50 = Some important claims are unsupported.
0.25 = Most claims are unsupported.
0.0 = Answer is unsupported or contradicts the context.

2. Relevancy:
Does the predicted answer directly answer the question?

Scoring:
1.0 = Directly answers the question.
0.75 = Mostly answers the question.
0.50 = Partially answers the question.
0.25 = Barely addresses the question.
0.0 = Does not answer the question.

3. Context Recall:
Does the retrieved context contain the information needed
to answer the question according to the reference answer?

Scoring:
1.0 = All important information is present.
0.75 = Most important information is present.
0.50 = Some important information is present.
0.25 = Very little information is present.
0.0 = Required information is absent.

IMPORTANT:
- Evaluate each metric independently.
- Do NOT automatically give 1.0.
- Give partial scores when appropriate.
- Do not use outside knowledge.
- Return ONLY valid JSON.

Return exactly:

{{
    "faithfulness": 0.0,
    "relevancy": 0.0,
    "context_recall": 0.0
}}
"""

    try:
        print(f"🤖 Evaluation model: {EVALUATOR_MODEL}")

        response = None
        last_error = None
        for model_instance in evaluator_llm:
            try:
                response = model_instance.invoke(prompt)
                if response and response.content:
                    break
            except Exception as error:
                last_error = error

        if not response or not response.content:
            raise RuntimeError(
                f"All evaluator models failed to respond: {last_error}"
            )

        if not response or not response.content:
            raise RuntimeError("Evaluator returned an empty response.")

        content = response.content

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            return content[0]["text"].strip()

        return str(content).strip()

    except Exception as e:
        raise RuntimeError(
            f"RAG evaluation failed using {EVALUATOR_MODEL}: {e}"
        )
# ============================================================
# CLEAN GEMINI JSON RESPONSE
# ============================================================

def clean_json_response(text: str) -> str:
    """
    Remove Markdown code fences if Gemini returns:

    ```json
    {...}
    ```
    """

    text = text.strip()

    # Remove opening JSON code fence.
    if text.startswith("```json"):
        text = text[7:]

    # Remove generic opening code fence.
    elif text.startswith("```"):
        text = text[3:]

    # Remove closing code fence.
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ============================================================
# RUN RAG EVALUATION
# ============================================================

def run_rag_eval(
    qa_list,
    retriever,
    output_csv="evaluation_results_gemini.csv"
):
    """
    Run every generated question through the actual RAG system.

    For every question we save:
    - question
    - prediction
    - ground truth
    - retrieved contexts
    - role
    - source
    - evaluation metrics
    """

    # Create the actual RAG chain that we want to test.
    # qa_chain = RetrievalQA.from_chain_type(
    #     llm=model,
    #     retriever=retriever,
    #     return_source_documents=True
    # )

    results = []

    # Evaluate every question.
    for index, qa in enumerate(qa_list):

        print(
            f"\nEvaluating question "
            f"{index + 1}/{len(qa_list)}"
        )

        question = qa["question"]

        # Original document chunk used as reference.
        ground_truth = qa["answer"]

        # Get role and source from the generated QA dataset.
        role = qa.get("role", "")
        source = qa.get("source", "")

        try:

            source_documents = retriever.invoke(
                question
            )
            predicted = generate_answer(
                question,
                source_documents
            )
            contexts = "\n---\n".join(
                doc.page_content
                for doc in source_documents
            )

            # ------------------------------------------------
            # ASK GEMINI TO EVALUATE THE RAG ANSWER
            # ------------------------------------------------

            raw_scores = evaluate_with_gemini(
                question=question,
                predicted_answer=predicted,
                retrieved_contexts=contexts,
                reference_answer=ground_truth
            )

            # Clean possible Markdown fences.
            cleaned_scores = clean_json_response(
                raw_scores
            )

            # Convert JSON string into Python dictionary.
            scores = json.loads(
                cleaned_scores
            )

        except Exception as e:

            print(
                f"Evaluation failed: {e}"
            )

            # Keep the evaluation running even if
            # one question fails.
            predicted = ""
            contexts = ""

            scores = {
                "faithfulness": None,
                "relevancy": None,
                "context_recall": None,
                "error": str(e)
            }

        # ----------------------------------------------------
        # SAVE THIS QUESTION'S COMPLETE RESULT
        # ----------------------------------------------------

        results.append({
            "question": question,
            "prediction": predicted,
            "ground_truth": ground_truth,
            "contexts": contexts,
            "role": role,
            "source": source,
            "metrics": json.dumps(scores)
        })

        # Small delay between evaluation requests.
        time.sleep(1)

    # Convert all results into DataFrame.
    results_df = pd.DataFrame(results)

    # Save evaluation results.
    results_df.to_csv(
        output_csv,
        index=False
    )

    print(
        f"\nEvaluation results saved to: {output_csv}"
    )

    return results


# ============================================================
# MAIN EXECUTION
# ============================================================

# if __name__ == "__main__":

#     # --------------------------------------------------------
#     # STEP 1:
#     # Retrieve many chunks to create evaluation questions.
#     # --------------------------------------------------------

#     docs = vectorstore.similarity_search(
#         "finance",
#         k=10
#     )

#     print(
#         f"Retrieved {len(docs)} chunks "
#         f"for evaluation dataset."
#     )

#     # --------------------------------------------------------
#     # STEP 2:
#     # Generate synthetic evaluation questions.
#     # --------------------------------------------------------

# #     qa_list = generate_qa_dataset(
# #     docs,
# #     output_csv=EVALUATOR_DIR / "qa_pairs_gemini.csv"
# # )

#     # --------------------------------------------------------
#     # STEP 3:
#     # Create the retriever used by the real RAG system.
#     # --------------------------------------------------------

#     retriever = vectorstore.as_retriever(
#         search_kwargs={
#             "k": 4
#         }
#     )

#     # --------------------------------------------------------
#     # STEP 4:
#     # Run RAG evaluation.
#     # --------------------------------------------------------

#     run_rag_eval(
#     qa_list,
#     retriever,
#     output_csv=EVALUATOR_DIR / "evaluation_results_gemini.csv"
# )

#     print("\nRAG evaluation completed successfully.")



if __name__ == "__main__":

    # ========================================================
    # CONFIGURATION
    # ========================================================

    # False = use existing QA dataset
    # True  = generate a new QA dataset first
    GENERATE_NEW_QA = False

    QA_FILE = EVALUATOR_DIR / "qa_pairs_gemini.csv"
    EVALUATION_FILE = EVALUATOR_DIR / "evaluation_results_gemini.csv"


    # ========================================================
    # STEP 1: QA DATASET
    # ========================================================

    if GENERATE_NEW_QA:

        print("\n🆕 Generating new QA dataset...")

        # Retrieve chunks from your vector database
        docs = vectorstore.similarity_search(
            "finance",
            k=10
        )

        print(
            f"📚 Retrieved {len(docs)} chunks "
            f"for QA generation."
        )

        # Generate QA dataset
        qa_list = generate_qa_dataset(
            docs,
            output_csv=QA_FILE
        )

        print(
            f"✅ Generated {len(qa_list)} QA pairs."
        )

    else:

        # ====================================================
        # USE EXISTING QA DATASET
        # ====================================================

        if not QA_FILE.exists():
            raise FileNotFoundError(
                f"""
QA dataset not found:

{QA_FILE}

Set:

GENERATE_NEW_QA = True

to generate it first.
"""
            )

        print(
            f"\n📂 Loading existing QA dataset:\n"
            f"{QA_FILE}"
        )

        qa_df = pd.read_csv(QA_FILE)
        qa_df = qa_df.head(20)

        qa_list = qa_df.to_dict(
            orient="records"
        )
        

        print(
            f"✅ Loaded {len(qa_list)} "
            f"existing evaluation questions."
        )


    # ========================================================
    # STEP 2: CREATE RAG RETRIEVER
    # ========================================================

    print("\n🔎 Creating RAG retriever...")
    retriever = get_rag_chain(role)

    # retriever = vectorstore.as_retriever(
    #     search_kwargs={
    #         "k": 4
    #     }
    # )


    # ========================================================
    # STEP 3: RUN EVALUATION
    # ========================================================

    print("\n🚀 Starting RAG evaluation...")

    run_rag_eval(
        qa_list,
        retriever,
        output_csv=EVALUATION_FILE
    )

    print(
        "\n✅ RAG evaluation completed successfully."
    )
