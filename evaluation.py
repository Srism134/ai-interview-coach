# evaluation.py
# Evaluates individual interview answers using rule-based heuristics. Fully offline.

import re
from utils import clamp

# ── Role-Specific Technical Keyword Sets ──────────────────────────────────────

TECHNICAL_KEYWORDS = {
    "Data Scientist": [
        "model", "feature", "training", "accuracy", "precision", "recall", "f1",
        "overfitting", "underfitting", "regularisation", "regularization",
        "cross-validation", "bias", "variance", "gradient", "loss", "metric",
        "distribution", "hypothesis", "p-value", "confidence interval",
        "regression", "classification", "clustering", "neural", "ensemble",
        "random forest", "boosting", "bagging", "pca", "dimensionality",
        "imputation", "normalisation", "normalization", "standardisation",
        "auc", "roc", "confusion matrix", "hyperparameter", "pipeline",
        "a/b test", "experiment", "statistical", "correlation", "causation",
    ],
    "Software Engineer (SDE)": [
        "time complexity", "space complexity", "big o", "algorithm", "data structure",
        "hash", "tree", "graph", "queue", "stack", "heap", "linked list",
        "cache", "database", "sql", "index", "api", "rest", "microservice",
        "concurrency", "thread", "async", "latency", "throughput", "scalability",
        "load balancer", "cap theorem", "distributed", "consistency", "availability",
        "design pattern", "solid", "refactor", "unit test", "integration test",
        "ci/cd", "deployment", "docker", "kubernetes", "version control",
    ],
    "ML Engineer": [
        "pipeline", "feature store", "model serving", "inference", "latency",
        "batch", "real-time", "mlops", "drift", "monitoring", "retraining",
        "experiment tracking", "model registry", "containerise", "containerize",
        "quantisation", "quantization", "onnx", "triton", "kubernetes", "docker",
        "training", "validation", "deployment", "shadow", "canary", "rollback",
        "skew", "data quality", "etl", "orchestration", "airflow", "kubeflow",
        "model performance", "a/b testing", "feature engineering", "versioning",
    ],
    "Product Manager": [
        "roadmap", "priority", "stakeholder", "metric", "kpi", "north star",
        "user research", "customer", "hypothesis", "mvp", "iteration",
        "agile", "sprint", "backlog", "trade-off", "tradeoff", "impact",
        "effort", "revenue", "retention", "engagement", "funnel", "conversion",
        "a/b test", "feature flag", "launch", "success criteria", "okr",
    ],
    "Data Analyst": [
        "sql", "query", "join", "aggregate", "window function", "cte",
        "data quality", "validation", "outlier", "distribution", "cohort",
        "funnel", "retention", "engagement", "statistical", "significance",
        "p-value", "confidence", "hypothesis", "visualisation", "visualization",
        "dashboard", "insight", "trend", "seasonality", "correlation",
        "etl", "pipeline", "tableau", "looker", "excel", "python", "pandas",
    ],
}

# Fallback generic keywords if role not found
GENERIC_KEYWORDS = ["result", "impact", "approach", "solution", "implement",
                    "analyse", "analyze", "measure", "improve", "design"]

# ── Structural Signal Patterns ─────────────────────────────────────────────────

# STAR method signals
STAR_SIGNALS = {
    "situation": ["situation", "context", "background", "working at", "was tasked", "our team"],
    "task": ["task", "goal", "objective", "needed to", "responsibility", "challenge was"],
    "action": ["so i", "i decided", "i implemented", "i built", "i designed", "i worked",
               "my approach", "i first", "then i", "i used", "i created", "i wrote"],
    "result": ["result", "outcome", "achieved", "improved", "reduced", "increased",
               "led to", "this meant", "as a result", "ultimately", "in the end",
               "%", "percent", "times faster", "x faster", "x improvement"],
}

# Confidence signals (positive = shows conviction, negative = hedging)
POSITIVE_CONFIDENCE = ["i decided", "i chose", "my approach", "i believe", "clearly",
                       "specifically", "the key insight", "i found that", "i determined"]
NEGATIVE_CONFIDENCE = ["i think maybe", "not sure", "i guess", "kind of", "sort of",
                       "i don't really know", "not totally sure", "i might be wrong",
                       "i'm not sure if", "probably maybe"]

# Communication structure signals
STRUCTURE_SIGNALS = ["first", "second", "third", "finally", "in summary", "to summarise",
                     "to summarize", "firstly", "secondly", "lastly", "in conclusion",
                     "the main point", "importantly", "specifically", "for example",
                     "for instance", "such as", "because", "therefore", "however"]


# ── Scoring Heuristics ─────────────────────────────────────────────────────────

def _score_clarity(answer: str) -> int:
    """
    Score 0-10 based on answer length, structure signals, and coherence.
    """
    words = answer.split()
    word_count = len(words)

    # Base score from length (too short or too long loses points)
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
        base = 7  # overly long answers can lose clarity

    lower = answer.lower()

    # Bonus: structural signposting
    structure_hits = sum(1 for s in STRUCTURE_SIGNALS if s in lower)
    structure_bonus = min(structure_hits, 3)

    # Bonus: uses concrete numbers or percentages
    has_numbers = bool(re.search(r'\b\d+[\.,]?\d*\s*(%|x\b|times|ms|seconds|hours|days|users|requests)', lower))
    number_bonus = 1 if has_numbers else 0

    # Penalty: very repetitive (same word > 5 times in short answer)
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


def _score_technical(answer: str, role: str) -> int:
    """
    Score 0-10 based on presence of domain-relevant technical keywords.
    """
    lower = answer.lower()
    keywords = TECHNICAL_KEYWORDS.get(role, GENERIC_KEYWORDS)

    hits = sum(1 for kw in keywords if kw in lower)
    word_count = len(answer.split())

    # Density: hits per 100 words (so longer answers aren't unfairly penalised)
    if word_count > 0:
        density = (hits / word_count) * 100
    else:
        density = 0

    # Map density to score
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

    # Absolute keyword count bonus for long, technically rich answers
    if hits >= 6:
        base = min(base + 1, 10)

    return int(clamp(base, 1, 10))


def _score_communication(answer: str) -> int:
    """
    Score 0-10 based on STAR method coverage, use of examples, and structure.
    """
    lower = answer.lower()
    star_coverage = 0

    for component, signals in STAR_SIGNALS.items():
        if any(s in lower for s in signals):
            star_coverage += 1

    # Base from STAR coverage (0-4 components)
    base = {0: 3, 1: 4, 2: 6, 3: 8, 4: 9}.get(star_coverage, 3)

    # Bonus: uses concrete example ("for example", "for instance", "specifically")
    example_bonus = 1 if any(s in lower for s in ["for example", "for instance", "specifically"]) else 0

    # Bonus: uses first-person ownership ("I did X") rather than passive
    ownership = len(re.findall(r'\bi\s+(built|designed|implemented|created|decided|chose|led|wrote|ran|tested)', lower))
    ownership_bonus = min(ownership, 2)

    # Penalty: answer is a bullet-point dump with no narrative
    bullet_count = answer.count('\n-') + answer.count('\n•') + answer.count('\n*')
    bullet_penalty = 1 if bullet_count > 5 else 0

    score = base + example_bonus + ownership_bonus - bullet_penalty
    return int(clamp(score, 1, 10))


def _score_confidence(answer: str) -> int:
    """
    Score 0-10 based on conviction signals vs hedging language.
    """
    lower = answer.lower()

    positive_hits = sum(1 for s in POSITIVE_CONFIDENCE if s in lower)
    negative_hits = sum(1 for s in NEGATIVE_CONFIDENCE if s in lower)

    # Count definitive statements (subject + strong verb)
    definitive = len(re.findall(
        r'\b(i (decided|chose|built|implemented|led|designed|realised|realized|concluded|determined))\b',
        lower
    ))

    # Count hedges
    hedge_patterns = r'\b(maybe|perhaps|might|could possibly|not sure|i think|i guess|kind of|sort of)\b'
    hedge_count = len(re.findall(hedge_patterns, lower))

    base = 6
    score = base + positive_hits + min(definitive, 2) - negative_hits - min(hedge_count, 3)
    return int(clamp(score, 1, 10))


def _generate_feedback(answer: str, question: str, role: str,
                       clarity: int, technical: int,
                       communication: int, confidence: int) -> str:
    """
    Generate a readable, specific feedback string from scores and answer signals.
    """
    parts = []
    lower = answer.lower()
    word_count = len(answer.split())

    # Clarity feedback
    if clarity >= 8:
        parts.append("Your answer was well-structured and easy to follow.")
    elif clarity >= 6:
        parts.append("Your answer covered the topic reasonably well.")
    elif word_count < 40:
        parts.append("Your answer was quite brief — try to elaborate with more detail and context.")
    else:
        parts.append("Try to structure your answer more clearly using signpost phrases like 'first', 'then', and 'as a result'.")

    # Technical feedback
    if technical >= 8:
        parts.append("You demonstrated strong domain knowledge with relevant technical depth.")
    elif technical >= 6:
        parts.append("Good use of relevant concepts — adding one or two more specific examples would strengthen this.")
    else:
        parts.append("Try to include more domain-specific concepts or terminology to demonstrate technical depth.")

    # STAR / communication feedback
    star_coverage = sum(
        1 for _, signals in STAR_SIGNALS.items() if any(s in lower for s in signals)
    )
    if communication >= 8:
        parts.append("You used a clear narrative structure that made your answer compelling.")
    elif star_coverage < 2:
        parts.append("Consider using the STAR method (Situation → Task → Action → Result) to frame your answer — it makes responses much clearer.")
    else:
        parts.append("Good structure — quantifying your results with numbers or percentages would make the impact even clearer.")

    # Confidence feedback
    if confidence >= 8:
        parts.append("You communicated with strong conviction and ownership.")
    elif confidence < 5:
        hedge_count = len(re.findall(
            r'\b(maybe|perhaps|not sure|i guess|kind of|sort of)\b', lower
        ))
        if hedge_count > 1:
            parts.append("Reduce hedging language ('maybe', 'I guess', 'sort of') — own your experience and decisions with confidence.")
        else:
            parts.append("Be more direct — state what you did and decided rather than what 'could' or 'might' have been done.")

    return " ".join(parts)


def _generate_improved_answer(question: str, role: str) -> str:
    """
    Return a structural template for a strong answer to this type of question.
    """
    q_lower = question.lower()

    if any(w in q_lower for w in ["time", "tell me about", "describe a", "walk me through a", "example of"]):
        return (
            "A strong answer would follow the STAR method: "
            "(1) Situation — briefly set the context (team, company stage, constraints); "
            "(2) Task — what specifically was your responsibility; "
            "(3) Action — detail the concrete steps you personally took, including tools and reasoning; "
            "(4) Result — quantify the outcome (e.g., '30% reduction in latency', '2x increase in precision'). "
            "Aim for 2-3 minutes of spoken content with one concrete metric."
        )
    elif any(w in q_lower for w in ["how would you", "how do you", "design", "approach", "build"]):
        return (
            "A strong answer would: "
            "(1) Clarify assumptions and constraints upfront; "
            "(2) Outline your high-level approach before diving into details; "
            "(3) Walk through your reasoning step-by-step, calling out tradeoffs explicitly; "
            "(4) Mention how you'd validate or measure success. "
            "Use concrete tools, techniques, or frameworks you've actually used."
        )
    elif any(w in q_lower for w in ["explain", "what is", "difference between", "define"]):
        return (
            "A strong answer would: "
            "(1) Give a concise, precise definition in your own words; "
            "(2) Explain the intuition behind it (why it works); "
            "(3) Give a concrete real-world example from your experience; "
            "(4) Mention edge cases or when this concept does/doesn't apply. "
            "Avoid reciting a textbook definition — show you truly understand it."
        )
    else:
        return (
            "A strong answer is specific, uses real examples with measurable outcomes, "
            "demonstrates clear reasoning, and shows ownership of decisions made. "
            "Where possible, quantify your impact (time saved, accuracy gained, revenue impact)."
        )


# ── Default Fallback ───────────────────────────────────────────────────────────

def _default_evaluation(question: str, answer: str) -> dict:
    return {
        "clarity": 5,
        "technical": 5,
        "communication": 5,
        "confidence": 5,
        "feedback": "Unable to evaluate automatically. Please review your answer manually.",
        "improved_answer": "A strong answer would include specific examples, measurable outcomes, technical depth, and clear structure (Situation → Task → Action → Result).",
        "question": question,
        "answer": answer,
    }


# ── Main Evaluation Function ───────────────────────────────────────────────────

def evaluate_answer(answer: str, question: str, role: str = "General") -> dict:
    """
    Evaluate a candidate's answer using rule-based heuristics. Fully offline.

    Args:
        answer: The candidate's answer text.
        question: The interview question that was asked.
        role: The target role (used for technical keyword matching).

    Returns:
        dict with keys: clarity, technical, communication, confidence,
                        feedback, improved_answer, question, answer
    """
    if not answer or len(answer.strip()) < 5:
        result = _default_evaluation(question, answer)
        result["feedback"] = "No answer provided."
        return result

    # Normalise role for keyword lookup
    matched_role = role
    if role not in TECHNICAL_KEYWORDS:
        for key in TECHNICAL_KEYWORDS:
            if role.lower() in key.lower() or key.lower() in role.lower():
                matched_role = key
                break

    clarity      = _score_clarity(answer)
    technical    = _score_technical(answer, matched_role)
    communication = _score_communication(answer)
    confidence   = _score_confidence(answer)

    feedback = _generate_feedback(
        answer, question, matched_role,
        clarity, technical, communication, confidence
    )
    improved = _generate_improved_answer(question, matched_role)

    return {
        "clarity":       int(clamp(clarity, 0, 10)),
        "technical":     int(clamp(technical, 0, 10)),
        "communication": int(clamp(communication, 0, 10)),
        "confidence":    int(clamp(confidence, 0, 10)),
        "feedback":      feedback,
        "improved_answer": improved,
        "question":      question,
        "answer":        answer,
    }


# ── Composite Score ────────────────────────────────────────────────────────────

def answer_composite_score(evaluation: dict) -> float:
    """
    Compute a single 0-100 composite score for one answer.
    Weights: technical 30%, communication 25%, confidence 20%, clarity 25%
    """
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
    """Format an evaluation dict into a readable markdown string."""
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
    """Return a label for a 0-100 score."""
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Needs Work"
