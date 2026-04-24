# scoring.py
# Final interview score computation and improvement plan generation. Fully offline.

from utils import clamp, scores_to_summary
from evaluation import answer_composite_score

WEIGHTS = {
    "technical":     0.30,
    "communication": 0.25,
    "confidence":    0.20,
    "clarity":       0.25,
}

PROBABILITY_BANDS = [
    (80, 100, "High",   "🟢", "Strong candidate — very likely to advance"),
    (60,  79, "Medium", "🟡", "Competitive candidate — may advance with polish"),
    (0,   59, "Low",    "🔴", "Needs more preparation before next round"),
]


def _get_probability(score: float) -> tuple:
    for lo, hi, label, icon, note in PROBABILITY_BANDS:
        if lo <= score <= hi:
            return label, icon, note
    return "Low", "🔴", "Needs more preparation before next round"


def calculate_score(all_evaluations: list, role: str = "AI Engineer") -> dict:
    if not all_evaluations:
        return _empty_score()

    totals = {k: 0.0 for k in WEIGHTS}
    for ev in all_evaluations:
        for k in WEIGHTS:
            totals[k] += float(ev.get(k, 5))

    n = len(all_evaluations)
    averages = {k: totals[k] / n for k in WEIGHTS}
    raw_score = sum(averages[k] * WEIGHTS[k] * 10 for k in WEIGHTS)
    final_score = int(round(clamp(raw_score, 0, 100)))
    per_answer = [answer_composite_score(ev) for ev in all_evaluations]
    prob_label, prob_icon, prob_note = _get_probability(final_score)

    return {
        "final_score":       final_score,
        "probability":       prob_label,
        "probability_icon":  prob_icon,
        "probability_note":  prob_note,
        "dimension_scores":  {k: round(averages[k] * 10, 1) for k in WEIGHTS},
        "per_answer_scores": per_answer,
        "strengths":         _default_strengths(averages)[:3],
        "weaknesses":        _default_weaknesses(averages)[:3],
        "improvement_plan":  _default_plan(averages)[:3],
        "num_questions":     n,
    }


def _empty_score() -> dict:
    return {
        "final_score": 0, "probability": "Low", "probability_icon": "🔴",
        "probability_note": "No answers to score.",
        "dimension_scores": {k: 0 for k in WEIGHTS},
        "per_answer_scores": [], "strengths": [],
        "weaknesses": ["No answers provided."], "improvement_plan": [], "num_questions": 0,
    }


def _default_strengths(averages: dict) -> list:
    strengths = []
    if averages["technical"] >= 7:
        strengths.append("Demonstrates strong, consistent technical depth across AI/ML concepts")
    elif averages["technical"] >= 5:
        strengths.append("Shows solid foundational understanding of core AI engineering concepts")
    if averages["communication"] >= 7:
        strengths.append("Communicates complex AI ideas clearly with good narrative structure")
    elif averages["communication"] >= 5:
        strengths.append("Provides reasonably well-structured, easy-to-follow responses")
    if averages["confidence"] >= 7:
        strengths.append("Answers with strong conviction and clear ownership of technical decisions")
    elif averages["confidence"] >= 5:
        strengths.append("Maintains a confident, professional tone throughout the interview")
    if averages["clarity"] >= 7:
        strengths.append("Organises answers logically with concrete examples and quantified outcomes")
    if not strengths:
        strengths = [
            "Engaged with all questions and attempted to address each one",
            "Showed willingness to work through technically challenging problems",
            "Provided relevant technical context in responses",
        ]
    return strengths[:3]


def _default_weaknesses(averages: dict) -> list:
    weaknesses = []
    ranked = sorted(WEIGHTS.keys(), key=lambda k: averages[k])
    detail = {
        "technical": (5.5,
            "Technical depth needs improvement — practise explaining LLM internals, RAG pipelines, "
            "and MLOps workflows out loud daily, naming specific tools and tradeoffs"),
        "communication": (5.5,
            "Answer structure can be tightened — use STAR for behavioural questions and "
            "step-by-step reasoning for technical ones; always close with a concrete outcome"),
        "confidence": (5.5,
            "Eliminate hedging phrases ('I think maybe', 'I guess', 'kind of') — own your "
            "technical decisions directly: 'I chose X because Y, which resulted in Z'"),
        "clarity": (5.5,
            "Improve clarity by using signpost phrases and quantifying every outcome — "
            "e.g., 'latency dropped 40%', 'retrieval precision improved from 62% to 81%'"),
    }
    for dim in ranked:
        threshold, message = detail[dim]
        if averages[dim] < threshold:
            weaknesses.append(message)
    if not weaknesses:
        weaknesses = ["Continue mock interview practice to add more depth and quantified outcomes to answers"]
    return weaknesses[:3]


def _default_plan(averages: dict) -> list:
    ranked = sorted(WEIGHTS.keys(), key=lambda k: averages[k])
    templates = {
        "technical": {
            "area": "Technical Depth — AI/ML & LLM Engineering",
            "action": "30 min daily: read one paper or blog on LLMs, RAG, or MLOps, then build a "
                      "hands-on mini-project (e.g., RAG pipeline with LangChain, model API with FastAPI+Docker). "
                      "Explain each concept aloud without notes until fluent.",
            "timeline": "3 weeks",
        },
        "communication": {
            "area": "Answer Structure — STAR & Technical Storytelling",
            "action": "Write STAR answers for 5 behavioural questions per day. For technical questions, "
                      "practise the pattern: clarify → high-level approach → tradeoffs → validation. "
                      "Record yourself and review for structure and flow.",
            "timeline": "1 week",
        },
        "confidence": {
            "area": "Confidence & Technical Ownership",
            "action": "Record yourself answering 5 questions daily. Scan recordings for filler words and hedges. "
                      "Replace every hedge with a direct assertion. Practise: 'I decided X because Y, "
                      "which led to Z' — not 'we might consider X'.",
            "timeline": "1 week",
        },
        "clarity": {
            "area": "Clarity, Conciseness & Quantification",
            "action": "Practise 90-second timed answers. Bullet-point mentally before speaking. "
                      "Always close with a concrete metric. If you can't quantify the result, "
                      "dig deeper into that project until you can.",
            "timeline": "1 week",
        },
    }
    return [templates[dim] for dim in ranked[:3]]
