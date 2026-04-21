# scoring.py
# Final interview score computation and improvement plan generation. Fully offline.

from utils import clamp, scores_to_summary
from evaluation import answer_composite_score

# ── Score Weights ──────────────────────────────────────────────────────────────

WEIGHTS = {
    "technical":     0.30,
    "communication": 0.25,
    "confidence":    0.20,
    "clarity":       0.25,
}

# ── Selection Probability Bands ────────────────────────────────────────────────

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


# ── Main Scoring Function ──────────────────────────────────────────────────────

def calculate_score(all_evaluations: list, role: str = "General") -> dict:
    """
    Compute final interview score from a list of answer evaluations.
    Fully offline — no LLM calls.

    Args:
        all_evaluations: List of evaluation dicts from evaluate_answer().
        role: Target role for context in improvement plan.

    Returns:
        {
            "final_score": int (0-100),
            "probability": "Low" | "Medium" | "High",
            "probability_icon": str,
            "probability_note": str,
            "dimension_scores": {technical, communication, confidence, clarity},
            "per_answer_scores": [float, ...],
            "strengths": [str, str, str],
            "weaknesses": [str, str, str],
            "improvement_plan": [{area, action, timeline}, ...],
            "num_questions": int,
        }
    """
    if not all_evaluations:
        return _empty_score()

    # ── Compute dimension averages ──
    totals = {k: 0.0 for k in WEIGHTS}
    for ev in all_evaluations:
        for k in WEIGHTS:
            totals[k] += float(ev.get(k, 5))

    n = len(all_evaluations)
    averages = {k: totals[k] / n for k in WEIGHTS}

    # ── Weighted final score (0-100) ──
    raw_score = sum(averages[k] * WEIGHTS[k] * 10 for k in WEIGHTS)
    final_score = int(round(clamp(raw_score, 0, 100)))

    # ── Per-answer composite scores ──
    per_answer = [answer_composite_score(ev) for ev in all_evaluations]

    # ── Selection probability ──
    prob_label, prob_icon, prob_note = _get_probability(final_score)

    # ── Strengths, weaknesses, improvement plan (rule-based) ──
    strengths        = _default_strengths(averages)
    weaknesses       = _default_weaknesses(averages)
    improvement_plan = _default_plan(averages)

    return {
        "final_score":       final_score,
        "probability":       prob_label,
        "probability_icon":  prob_icon,
        "probability_note":  prob_note,
        "dimension_scores":  {k: round(averages[k] * 10, 1) for k in WEIGHTS},
        "per_answer_scores": per_answer,
        "strengths":         strengths[:3],
        "weaknesses":        weaknesses[:3],
        "improvement_plan":  improvement_plan[:3],
        "num_questions":     n,
    }


# ── Fallback / Rule-Based Data ─────────────────────────────────────────────────

def _empty_score() -> dict:
    return {
        "final_score":       0,
        "probability":       "Low",
        "probability_icon":  "🔴",
        "probability_note":  "No answers to score.",
        "dimension_scores":  {k: 0 for k in WEIGHTS},
        "per_answer_scores": [],
        "strengths":         [],
        "weaknesses":        ["No answers provided."],
        "improvement_plan":  [],
        "num_questions":     0,
    }


def _default_strengths(averages: dict) -> list:
    strengths = []
    if averages["technical"] >= 7:
        strengths.append("Demonstrates strong and consistent technical knowledge")
    elif averages["technical"] >= 5:
        strengths.append("Shows solid foundational technical understanding")

    if averages["communication"] >= 7:
        strengths.append("Communicates ideas clearly and with good structure")
    elif averages["communication"] >= 5:
        strengths.append("Provides reasonably well-structured responses")

    if averages["confidence"] >= 7:
        strengths.append("Answers with conviction and clear ownership of decisions")
    elif averages["confidence"] >= 5:
        strengths.append("Generally maintains a confident and professional tone")

    if averages["clarity"] >= 7:
        strengths.append("Organises answers in a logical, easy-to-follow way")

    if not strengths:
        strengths = [
            "Attempted all questions and engaged throughout",
            "Showed willingness to work through difficult problems",
            "Provided relevant context in responses",
        ]
    return strengths[:3]


def _default_weaknesses(averages: dict) -> list:
    weaknesses = []

    # Sort dimensions from weakest first so most critical feedback comes first
    ranked = sorted(WEIGHTS.keys(), key=lambda k: averages[k])

    detail = {
        "technical": (
            5.5,
            "Technical depth needs improvement — practise explaining core "
            "concepts out loud and work through applied problems daily"
        ),
        "communication": (
            5.5,
            "Communication structure can be tightened — use the STAR method "
            "(Situation, Task, Action, Result) to frame every behavioural answer"
        ),
        "confidence": (
            5.5,
            "Answer confidence needs work — reduce hedging words "
            "('maybe', 'I guess') and practise owning your decisions directly"
        ),
        "clarity": (
            5.5,
            "Answer clarity can improve — use signpost phrases "
            "('first', 'then', 'as a result') and keep answers focused and concise"
        ),
    }

    for dim in ranked:
        threshold, message = detail[dim]
        if averages[dim] < threshold:
            weaknesses.append(message)

    if not weaknesses:
        weaknesses = ["Continue practising with mock interviews to maintain sharpness"]

    return weaknesses[:3]


def _default_plan(averages: dict) -> list:
    plan = []
    ranked = sorted(WEIGHTS.keys(), key=lambda k: averages[k])

    templates = {
        "technical": {
            "area":     "Technical Knowledge",
            "action":   "Study core concepts through official documentation and hands-on projects; "
                        "aim to explain each concept aloud without notes",
            "timeline": "2 weeks",
        },
        "communication": {
            "area":     "Answer Structure",
            "action":   "Practise the STAR method for every behavioural question; "
                        "write out answers first, then rehearse speaking them",
            "timeline": "1 week",
        },
        "confidence": {
            "area":     "Confidence & Delivery",
            "action":   "Record yourself answering common questions; "
                        "review recordings to identify and eliminate filler words and hedging",
            "timeline": "1 week",
        },
        "clarity": {
            "area":     "Clarity & Conciseness",
            "action":   "Practice giving timed answers (90 seconds max per question); "
                        "use bullet-point outlines before speaking to stay on track",
            "timeline": "1 week",
        },
    }

    for dim in ranked[:3]:
        plan.append(templates[dim])

    return plan
