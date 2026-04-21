# utils.py
# Helper functions: JSON parsing, session helpers, offline stubs

import json
import re
import streamlit as st


# ── Offline Stubs (replaces Anthropic API client) ─────────────────────────────

def get_client():
    """No-op: API removed. Kept for import compatibility."""
    return None


def call_llm(prompt: str, max_tokens: int = 1000, system: str = "") -> str:
    """
    Offline stub — always returns LLM_ERROR so every caller falls through
    to its built-in rule-based / static fallback path.
    No network calls are made.
    """
    return "LLM_ERROR: offline mode"


# ── JSON Parsing ───────────────────────────────────────────────────────────────

def safe_parse_json(text: str, fallback: dict = None) -> dict:
    """
    Safely parse JSON from a string.
    Strips markdown fences, finds the first JSON object/array.
    """
    if fallback is None:
        fallback = {}

    if not text or text.startswith("LLM_ERROR"):
        return fallback

    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract first {...} block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try to extract first [...] block
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return fallback


# ── Session State Helpers ──────────────────────────────────────────────────────

SESSION_DEFAULTS = {
    "phase": "setup",              # setup | interview | results
    "role": "Data Scientist",
    "resume_text": "",
    "parsed_resume": {},
    "questions": [],               # list of question strings
    "answers": [],                 # list of answer strings
    "feedbacks": [],               # list of evaluation dicts
    "current_question": "",
    "awaiting_answer": False,
    "interview_done": False,
    "final_score": None,           # final score dict
    "improvement_plan": None,      # improvement plan dict
    "question_count": 0,
    "max_questions": 5,
}


def init_session():
    """Initialize all session state keys with defaults if not present."""
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_session():
    """Clear all interview session state and return to setup."""
    for key in SESSION_DEFAULTS:
        st.session_state[key] = SESSION_DEFAULTS[key]


def get_session(key: str):
    """Safe getter for session state."""
    return st.session_state.get(key, SESSION_DEFAULTS.get(key))


def set_session(key: str, value):
    """Safe setter for session state."""
    st.session_state[key] = value


# ── Display Helpers ────────────────────────────────────────────────────────────

def score_color(score: float) -> str:
    """Return a color string based on score 0-100."""
    if score >= 75:
        return "#10b981"   # green
    elif score >= 55:
        return "#f59e0b"   # amber
    else:
        return "#ef4444"   # red


def probability_color(prob: str) -> str:
    """Return color for selection probability label."""
    colors = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}
    return colors.get(prob, "#9ca3af")


def clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def scores_to_summary(feedbacks: list) -> str:
    """Format evaluations into a readable summary string."""
    lines = []
    for i, ev in enumerate(feedbacks, 1):
        lines.append(
            f"Answer {i}: clarity={ev.get('clarity', 5)}, "
            f"technical={ev.get('technical', 5)}, "
            f"communication={ev.get('communication', 5)}, "
            f"confidence={ev.get('confidence', 5)}"
        )
    return "\n".join(lines)
