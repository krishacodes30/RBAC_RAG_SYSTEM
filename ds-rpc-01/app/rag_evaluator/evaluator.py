
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
