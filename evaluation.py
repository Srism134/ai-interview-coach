# evaluation.py
# Evaluates individual interview answers using rule-based heuristics. Fully offline.
# Tailored for AI Engineer role.

import re
from utils import clamp

# ── AI Engineer Technical Keyword Set ─────────────────────────────────────────

TECHNICAL_KEYWORDS = {
    "AI Engineer": [
        # ML fundamentals
        "bias", "variance", "overfitting", "underfitting", "regularisation", "regularization",
        "gradient descent", "adam", "sgd", "adamw", "loss function", "cross-entropy",
        "backpropagation", "learning rate", "batch size", "epoch", "convergence",
        "cross-validation", "hyperparameter", "ensemble", "random forest", "boosting",
        "xgboost", "lightgbm", "precision", "recall", "f1", "auc", "roc",
        "confusion matrix", "class imbalance", "smote", "transfer learning", "fine-tuning",
        # Deep learning
        "transformer", "attention", "self-attention", "multi-head attention",
        "encoder", "decoder", "embedding", "positional encoding", "layer norm",
        "batch norm", "dropout", "residual", "skip connection", "cnn", "rnn",
        "lstm", "gru", "diffusion", "vae", "gan", "distillation", "quantisation", "quantization",
        "pytorch", "tensorflow", "keras", "onnx", "triton",
        # LLM / GenAI
        "llm", "gpt", "bert", "rlhf", "dpo", "rag", "retrieval", "vector database",
        "embedding", "hallucination", "prompt", "chain-of-thought", "few-shot",
        "zero-shot", "lora", "qlora", "peft", "temperature", "top-p", "top-k",
        "langchain", "openai", "hugging face", "agent", "tool use", "react",
        "constitutional ai", "alignment", "guardrails",
        # MLOps / Deployment
        "mlops", "pipeline", "feature store", "model registry", "experiment tracking",
        "mlflow", "weights & biases", "wandb", "kubeflow", "airflow",
        "docker", "kubernetes", "ci/cd", "canary", "shadow deployment", "blue-green",
        "model drift", "data drift", "monitoring", "retraining", "serving",
        "inference", "latency", "throughput", "p99", "sla", "fastapi", "triton",
        "onnx runtime", "tensorrt", "model quantisation",
        # System design / infra
        "distributed training", "data parallelism", "model parallelism", "tensor parallelism",
        "pipeline parallelism", "gpu", "cuda", "hnsw", "faiss", "approximate nearest neighbour",
        "point-in-time", "feature engineering", "data leakage",
        # Python / coding
        "numpy", "pandas", "asyncio", "generator", "decorator", "gil", "multiprocessing",
        "type hint", "pydantic", "context manager", "complexity", "big o", "lru cache",
    ],
}

# Fallback
GENERIC_KEYWORDS = ["result", "impact", "approach", "solution", "implement",
                    "analyse", "analyze", "measure", "improve", "design"]

# ── Structural Signal Patterns ─────────────────────────────────────────────────

STAR_SIGNALS = {
    "situation": ["situation", "context", "background", "working at", "was tasked", "our team", "the problem was"],
    "task": ["task", "goal", "objective", "needed to", "responsibility", "challenge was", "i was asked to"],
    "action": ["so i", "i decided", "i implemented", "i built", "i designed", "i worked",
               "my approach", "i first", "then i", "i used", "i created", "i wrote", "i chose"],
    "result": ["result", "outcome", "achieved", "improved", "reduced", "increased",
               "led to", "this meant", "as a result", "ultimately", "in the end",
               "%", "percent", "times faster", "x faster", "x improvement", "latency dropped",
               "accuracy increased", "cost reduced"],
}

POSITIVE_CONFIDENCE = ["i decided", "i chose", "my approach", "i believe", "clearly",
                       "specifically", "the key insight", "i found that", "i determined",
                       "i demonstrated", "i proved"]
NEGATIVE_CONFIDENCE = ["i think maybe", "not sure", "i guess", "kind of", "sort of",
                       "i don't really know", "not totally sure", "i might be wrong",
                       "i'm not sure if", "probably maybe"]

STRUCTURE_SIGNALS = ["first", "second", "third", "finally", "in summary", "to summarise",
                     "to summarize", "firstly", "secondly", "lastly", "in conclusion",
                     "the main point", "importantly", "specifically", "for example",
                     "for instance", "such as", "because", "therefore", "however",
                     "on the other hand", "as a result", "this means"]


# ── Scoring Heuristics ─────────────────────────────────────────────────────────

def _score_clarity(answer: str) -> int:
    words = answer.split()
    word_count = len(words)

    if word_count < 20:
        base = 2
    elif word_count < 40:
        base = 4
    elif word_count < 80:
        base = 6
    elif word_count < 200:
        base = 7
    elif word_count < 400:
        base = 8
    else:
        base = 7

    lower = answer.lower()
    structure_hits = sum(1 for s in STRUCTURE_SIGNALS if s in lower)
    structure_bonus = min(structure_hits, 3)

    has_numbers = bool(re.search(
        r'\b\d+[\.,]?\d*\s*(%|x\b|times|ms|seconds|hours|days|users|requests|tokens|gb|mb|params)',
        lower
    ))
    number_bonus = 1 if has_numbers else 0

    if word_count < 100:
        word_freq = {}
        for w in words:
            w_clean = re.sub(r'[^a-z]', '', w.lower())
            if len(w_clean) > 4:
                word_freq[w_clean] = word_freq.get(w_clean, 0) + 1
        repetition_penalty = sum(1 for count in word_freq.values() if count > 4)
    else:
        repetition_penalty = 0

    score = base + structure_bonus + number_bonus - repetition_penalty
    return int(clamp(score, 1, 10))


def _score_technical(answer: str, role: str = "AI Engineer") -> int:
    lower = answer.lower()
    keywords = TECHNICAL_KEYWORDS.get(role, TECHNICAL_KEYWORDS.get("AI Engineer", GENERIC_KEYWORDS))

    hits = sum(1 for kw in keywords if kw in lower)
    word_count = len(answer.split())

    if word_count > 0:
        density = (hits / word_count) * 100
    else:
        density = 0

    if density >= 8:
        base = 9
    elif density >= 5:
        base = 8
    elif density >= 3:
        base = 7
    elif density >= 2:
        base = 6
    elif density >= 1:
        base = 5
    elif hits >= 2:
        base = 4
    elif hits == 1:
        base = 3
    else:
        base = 2

    if hits >= 6:
        base = min(base + 1, 10)

    return int(clamp(base, 1, 10))


def _score_communication(answer: str) -> int:
    lower = answer.lower()
    star_coverage = 0

    for component, signals in STAR_SIGNALS.items():
        if any(s in lower for s in signals):
            star_coverage += 1

    base = {0: 3, 1: 4, 2: 6, 3: 8, 4: 9}.get(star_coverage, 3)

    example_bonus = 1 if any(s in lower for s in ["for example", "for instance", "specifically", "concretely"]) else 0
    ownership = len(re.findall(
        r'\bi\s+(built|designed|implemented|created|decided|chose|led|wrote|ran|tested|deployed|trained|fine-tuned)',
        lower
    ))
    ownership_bonus = min(ownership, 2)

    score = base + example_bonus + ownership_bonus
    return int(clamp(score, 1, 10))


def _score_confidence(answer: str) -> int:
    lower = answer.lower()

    positive_hits = sum(1 for s in POSITIVE_CONFIDENCE if s in lower)
    negative_hits = sum(1 for s in NEGATIVE_CONFIDENCE if s in lower)

    base = 6
    base += min(positive_hits, 2)
    base -= min(negative_hits * 2, 4)

    # Passive voice penalty
    passive_count = len(re.findall(r'\b(was|were|been)\s+\w+ed\b', lower))
    if passive_count > 3:
        base -= 1

    return int(clamp(base, 1, 10))


# ── Feedback Generation ────────────────────────────────────────────────────────

def _generate_feedback(
    answer: str, question: str, role: str,
    clarity: int, technical: int, communication: int, confidence: int
) -> str:
    parts = []
    lower = answer.lower()

    composite = int((technical * 0.30 + communication * 0.25 + confidence * 0.20 + clarity * 0.25) * 10)

    if composite >= 80:
        parts.append("Strong answer overall.")
    elif composite >= 60:
        parts.append("Solid answer with some areas to sharpen.")
    else:
        parts.append("This answer needs more depth and specificity.")

    if technical >= 8:
        parts.append("Excellent technical depth — you demonstrated clear command of the concepts.")
    elif technical >= 6:
        parts.append("Good technical coverage — consider adding more precise terminology or explaining trade-offs explicitly.")
    elif technical < 5:
        parts.append("The answer lacked technical depth — for an AI Engineer role, you should reference specific algorithms, tools, or architectural choices.")

    if communication >= 8:
        parts.append("You used a clear narrative structure that made your answer easy to follow.")
    elif sum(1 for _, signals in STAR_SIGNALS.items() if any(s in lower for s in signals)) < 2:
        parts.append(
            "Use the STAR method (Situation → Task → Action → Result) to frame your answer — "
            "it gives interviewers a clear narrative arc to follow."
        )
    else:
        parts.append("Good structure — quantifying your results with numbers or percentages would sharpen the impact.")

    if confidence >= 8:
        parts.append("You answered with strong conviction and clear ownership.")
    elif confidence < 5:
        hedge_count = len(re.findall(r'\b(maybe|perhaps|not sure|i guess|kind of|sort of)\b', lower))
        if hedge_count > 1:
            parts.append(
                "Reduce hedging language ('maybe', 'I guess', 'sort of') — own your experience and decisions directly."
            )
        else:
            parts.append("Be more direct: state what you did and decided rather than what 'could' or 'might' have been done.")

    return " ".join(parts)


def _generate_improved_answer(question: str, role: str = "AI Engineer") -> str:
    q_lower = question.lower()

    if any(w in q_lower for w in ["tell me about", "describe a", "walk me through a", "time when"]):
        return (
            "A strong answer uses the STAR method: "
            "(1) Situation — set the scene briefly (team size, constraints, business context); "
            "(2) Task — your specific responsibility; "
            "(3) Action — concrete steps you personally took, tools and reasoning; "
            "(4) Result — quantify the outcome (e.g., '40% latency reduction', '2 points of F1 gain'). "
            "Aim for 2-3 minutes spoken with one clear metric."
        )
    elif any(w in q_lower for w in ["how would you", "how do you", "design", "build", "architect"]):
        return (
            "A strong answer: "
            "(1) Clarifies assumptions and constraints upfront; "
            "(2) Outlines the high-level approach before details; "
            "(3) Walks through reasoning step-by-step with explicit tradeoffs; "
            "(4) Names concrete tools, frameworks, or algorithms you've used; "
            "(5) Describes how you'd validate or monitor success in production."
        )
    elif any(w in q_lower for w in ["explain", "what is", "difference between", "define", "how does"]):
        return (
            "A strong answer: "
            "(1) Gives a concise, precise definition in your own words; "
            "(2) Explains the intuition (why it works mechanistically); "
            "(3) Provides a concrete real-world example from your experience; "
            "(4) Discusses edge cases or limitations. "
            "Avoid textbook recitation — show you truly understand the concept."
        )
    else:
        return (
            "A strong answer is specific, uses real examples with measurable outcomes, "
            "demonstrates clear reasoning, and shows ownership of decisions. "
            "Quantify impact wherever possible (latency saved, accuracy gained, cost reduced)."
        )


def _default_evaluation(question: str, answer: str) -> dict:
    return {
        "clarity": 5,
        "technical": 5,
        "communication": 5,
        "confidence": 5,
        "feedback": "Unable to evaluate automatically. Please review your answer manually.",
        "improved_answer": (
            "A strong answer would include specific examples, measurable outcomes, "
            "technical depth, and clear structure (Situation → Task → Action → Result)."
        ),
        "question": question,
        "answer": answer,
    }


# ── Main Evaluation Function ───────────────────────────────────────────────────

def evaluate_answer(answer: str, question: str, role: str = "AI Engineer") -> dict:
    """
    Evaluate a candidate's answer using rule-based heuristics. Fully offline.
    """
    if not answer or len(answer.strip()) < 5:
        result = _default_evaluation(question, answer)
        result["feedback"] = "No answer provided."
        return result

    clarity      = _score_clarity(answer)
    technical    = _score_technical(answer, "AI Engineer")
    communication = _score_communication(answer)
    confidence   = _score_confidence(answer)

    feedback = _generate_feedback(
        answer, question, "AI Engineer",
        clarity, technical, communication, confidence
    )
    improved = _generate_improved_answer(question, "AI Engineer")

    return {
        "clarity":        int(clamp(clarity, 0, 10)),
        "technical":      int(clamp(technical, 0, 10)),
        "communication":  int(clamp(communication, 0, 10)),
        "confidence":     int(clamp(confidence, 0, 10)),
        "feedback":       feedback,
        "improved_answer": improved,
        "question":       question,
        "answer":         answer,
    }


# ── Composite Score ────────────────────────────────────────────────────────────

def answer_composite_score(evaluation: dict) -> float:
    weights = {
        "technical":     0.30,
        "communication": 0.25,
        "confidence":    0.20,
        "clarity":       0.25,
    }
    score = sum(
        evaluation.get(k, 5) * w * 10
        for k, w in weights.items()
    )
    return round(clamp(score, 0, 100), 1)


# ── Formatted Display ──────────────────────────────────────────────────────────

def format_evaluation(evaluation: dict) -> str:
    c  = evaluation.get("clarity", 0)
    t  = evaluation.get("technical", 0)
    co = evaluation.get("communication", 0)
    cn = evaluation.get("confidence", 0)
    composite = answer_composite_score(evaluation)

    def bar(score, max_score=10):
        filled = int((score / max_score) * 10)
        return "█" * filled + "░" * (10 - filled)

    lines = [
        f"**📊 Answer Score: {composite}/100**",
        "",
        "| Dimension | Score | Bar |",
        "|---|---|---|",
        f"| Clarity | {c}/10 | `{bar(c)}` |",
        f"| Technical Accuracy | {t}/10 | `{bar(t)}` |",
        f"| Communication | {co}/10 | `{bar(co)}` |",
        f"| Confidence | {cn}/10 | `{bar(cn)}` |",
        "",
        f"**💬 Feedback:** {evaluation.get('feedback', '')}",
        "",
        f"**💡 Model Answer:** {evaluation.get('improved_answer', '')}",
    ]
    return "\n".join(lines)


def score_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Needs Work"
