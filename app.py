# app.py — AI Interview Coach (Production)
# Streamlit front-end for interview_engine.py
# Features: multi-role, adaptive difficulty, follow-up questions, scoring, no hardcoding

import streamlit as st
import time
import re
from interview_engine import (
    ALL_ROLES,
    CATEGORY_LABELS,
    CANONICAL_CATEGORIES,
    generate_question,
    generate_followup,
    get_opening_message,
    _to_scalar_score,
    _get_role_questions,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global font */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0f1117; }
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label { color: #aaa !important; font-size: 0.85rem; }

/* Chat messages */
.chat-user {
    background: #1e3a5f;
    border-left: 4px solid #4fa3e0;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 8px 0;
    color: #e8f4fd;
}
.chat-ai {
    background: #1a1f2e;
    border-left: 4px solid #7c3aed;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 8px 0;
    color: #e0e0f0;
}
.chat-system {
    background: #1a2a1a;
    border-left: 4px solid #22c55e;
    padding: 10px 16px;
    border-radius: 8px;
    margin: 8px 0;
    color: #bbf7d0;
    font-size: 0.9rem;
}
.score-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-left: 8px;
}
.score-high { background: #14532d; color: #86efac; }
.score-mid  { background: #713f12; color: #fde68a; }
.score-low  { background: #7f1d1d; color: #fca5a5; }
.diff-easy   { color: #4ade80; font-size: 0.75rem; font-weight: 600; }
.diff-medium { color: #facc15; font-size: 0.75rem; font-weight: 600; }
.diff-hard   { color: #f87171; font-size: 0.75rem; font-weight: 600; }
.stTextArea textarea {
    background: #1a1a2e !important;
    color: #e0e0ff !important;
    border: 1px solid #3a3a5c !important;
    border-radius: 8px !important;
}
.metric-card {
    background: #1a1f2e;
    border: 1px solid #2d3748;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Helpers ──────────────────────────────────────────────────────
def ss(key, default=None):
    """Get session state value with a default."""
    return st.session_state.get(key, default)


def set_ss(key, value):
    """Set session state value."""
    st.session_state[key] = value


def init_session():
    """Initialise all session state keys for a fresh interview."""
    defaults = {
        "role":                 ALL_ROLES[0],
        "interview_started":    False,
        "interview_complete":   False,
        "messages":             [],        # list of {role, content, meta}
        "current_question":     None,      # full question dict
        "asked_questions":      [],        # list of question strings asked
        "scores":               [],        # list of numeric scores 0-100
        "category_scores":      {},        # cat -> [scores]
        "question_count":       0,
        "max_questions":        10,
        "awaiting_followup":    False,
        "resume_text":          "",
        "total_score":          0,
        "answer_draft":         "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_interview(keep_role=True, keep_resume=True):
    """Reset interview state while optionally preserving role/resume."""
    role   = ss("role")
    resume = ss("resume_text")
    max_q  = ss("max_questions")

    keys_to_clear = [
        "interview_started", "interview_complete", "messages",
        "current_question", "asked_questions", "scores",
        "category_scores", "question_count", "awaiting_followup",
        "total_score", "answer_draft",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]

    init_session()

    if keep_role:
        set_ss("role", role)
    if keep_resume:
        set_ss("resume_text", resume)
    set_ss("max_questions", max_q)


init_session()


# ── Score Utilities ────────────────────────────────────────────────────────────
def score_answer_heuristic(answer: str, question_dict: dict) -> int:
    """
    Lightweight heuristic scoring (0-100) when no LLM is available.
    Criteria:
      - Length / depth      (0-30)
      - Technical keywords  (0-30)
      - Structure           (0-20)
      - Difficulty penalty  (0-20)
    """
    if not answer or not answer.strip():
        return 0

    words = answer.split()
    word_count = len(words)

    # Length score (max 30)
    length_score = min(30, int(word_count / 5))

    # Keyword score (max 30)
    tech_keywords = [
        "model", "data", "train", "deploy", "pipeline", "feature", "loss",
        "gradient", "layer", "embedding", "vector", "latency", "scalab",
        "docker", "kubernetes", "api", "metric", "monitor", "cache", "query",
        "retriev", "fine-tun", "inference", "backprop", "attention", "token",
        "cluster", "distribut", "algorithm", "complexit", "optim", "batch",
    ]
    answer_lower = answer.lower()
    kw_hits = sum(1 for kw in tech_keywords if kw in answer_lower)
    keyword_score = min(30, kw_hits * 3)

    # Structure score (max 20): presence of structure indicators
    structure_indicators = [
        "first", "second", "third", "because", "therefore", "however",
        "for example", "such as", "specifically", "in contrast", "additionally",
        "the reason", "this means", "as a result",
    ]
    struct_hits = sum(1 for ind in structure_indicators if ind in answer_lower)
    structure_score = min(20, struct_hits * 5)

    # Difficulty adjustment (max 20)
    difficulty = question_dict.get("difficulty", "medium")
    diff_bonus = {"easy": 20, "medium": 10, "hard": 5}
    difficulty_score = diff_bonus.get(difficulty, 10) if word_count > 30 else 0

    total = length_score + keyword_score + structure_score + difficulty_score
    return min(100, max(0, total))


def score_to_label(score: float) -> str:
    if score >= 75:
        return "Excellent"
    if score >= 55:
        return "Good"
    if score >= 35:
        return "Fair"
    return "Needs Work"


def score_badge_html(score: float) -> str:
    css = "score-high" if score >= 70 else ("score-mid" if score >= 45 else "score-low")
    label = score_to_label(score)
    return f'<span class="score-badge {css}">{score:.0f}/100 — {label}</span>'


def difficulty_badge_html(difficulty: str) -> str:
    return f'<span class="diff-{difficulty}">● {difficulty.upper()}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎯 AI Interview Coach")
        st.markdown("---")

        # ── Role selection ────────────────────────────────────────────────────
        st.markdown("#### 👤 Target Role")
        current_role = ss("role")
        role_idx = ALL_ROLES.index(current_role) if current_role in ALL_ROLES else 0
        selected_role = st.selectbox(
            "Select Role",
            options=ALL_ROLES,
            index=role_idx,
            key="role_selector",
            label_visibility="collapsed",
        )
        if selected_role != ss("role"):
            set_ss("role", selected_role)
            if ss("interview_started"):
                reset_interview(keep_role=True)
                st.rerun()

        # ── Question count ────────────────────────────────────────────────────
        st.markdown("#### 📋 Questions per Session")
        max_q = st.slider(
            "Number of questions",
            min_value=5,
            max_value=30,
            value=ss("max_questions"),
            step=5,
            key="max_q_slider",
            label_visibility="collapsed",
        )
        if max_q != ss("max_questions"):
            set_ss("max_questions", max_q)

        # ── Resume input ──────────────────────────────────────────────────────
        st.markdown("#### 📄 Resume / Background (optional)")
        resume_text = st.text_area(
            "Paste your resume keywords or summary",
            value=ss("resume_text"),
            height=100,
            placeholder="e.g. 5 years Python, PyTorch, deployed LLMs, Kubernetes...",
            label_visibility="collapsed",
            key="resume_input",
        )
        set_ss("resume_text", resume_text)

        st.markdown("---")

        # ── Session stats ─────────────────────────────────────────────────────
        if ss("interview_started"):
            q_count = ss("question_count")
            max_qs  = ss("max_questions")
            scores  = ss("scores")
            avg     = sum(scores) / len(scores) if scores else 0

            st.markdown("#### 📊 Session Stats")
            col1, col2 = st.columns(2)
            col1.metric("Questions", f"{q_count}/{max_qs}")
            col2.metric("Avg Score", f"{avg:.0f}/100" if scores else "—")

            if scores:
                pct = avg / 100
                bar_color = "#22c55e" if avg >= 70 else ("#facc15" if avg >= 45 else "#ef4444")
                st.markdown(
                    f"""<div style='background:#1a1f2e;border-radius:8px;padding:4px;margin-top:4px'>
                    <div style='background:{bar_color};width:{pct*100:.0f}%;height:8px;border-radius:6px'></div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("---")

        # ── Control buttons ───────────────────────────────────────────────────
        if not ss("interview_started"):
            if st.button("▶️ Start Interview", use_container_width=True, type="primary"):
                start_interview()
                st.rerun()
        else:
            if st.button("🔄 Restart Interview", use_container_width=True):
                reset_interview(keep_role=True)
                st.rerun()
            if st.button("⏭️ Skip Question", use_container_width=True):
                skip_question()
                st.rerun()

        # ── Question bank info ────────────────────────────────────────────────
        st.markdown("---")
        role = ss("role")
        role_qs = _get_role_questions(role)
        st.markdown(f"#### 📚 Question Bank")
        st.markdown(f"**{role}**: {len(role_qs)} questions")
        for cat in CANONICAL_CATEGORIES:
            cat_count = sum(1 for q in role_qs if q["category"] == cat)
            label = CATEGORY_LABELS.get(cat, cat)
            st.markdown(f"<small>• {label}: {cat_count}q</small>", unsafe_allow_html=True)


# ── Interview Logic ────────────────────────────────────────────────────────────
def start_interview():
    role = ss("role")
    opening = get_opening_message(role)
    add_message("assistant", opening, {"type": "opening"})
    set_ss("interview_started", True)
    ask_next_question()


def ask_next_question():
    role      = ss("role")
    resume    = ss("resume_text")
    asked     = ss("asked_questions")
    scores    = ss("scores")
    last_score = scores[-1] if scores else None

    q_dict = generate_question(
        role=role,
        resume_text=resume,
        previous_questions=asked,
        last_answer_score=last_score,
    )

    set_ss("current_question", q_dict)
    asked.append(q_dict["question"])
    set_ss("asked_questions", asked)
    set_ss("awaiting_followup", False)

    q_num  = ss("question_count") + 1
    max_qs = ss("max_questions")
    set_ss("question_count", q_num)

    cat_label = CATEGORY_LABELS.get(q_dict["category"], q_dict["category"])
    diff_html = difficulty_badge_html(q_dict["difficulty"])

    msg_content = (
        f"**Q{q_num} of {max_qs}** · {cat_label} · {diff_html}\n\n"
        f"{q_dict['question']}"
    )
    add_message("assistant", msg_content, {
        "type": "question",
        "question_num": q_num,
        "category": q_dict["category"],
        "difficulty": q_dict["difficulty"],
    })


def ask_followup(answer: str):
    q_dict = ss("current_question")
    last_score = ss("scores")[-1] if ss("scores") else None
    followup = generate_followup(q_dict, answer, last_score)
    set_ss("awaiting_followup", True)
    add_message("assistant", f"**Follow-up:** {followup}", {"type": "followup"})


def skip_question():
    if not ss("interview_started") or ss("interview_complete"):
        return
    add_message("system", "⏭️ Question skipped.", {"type": "skip"})
    _maybe_advance()


def _maybe_advance():
    """After handling an answer (or skip), decide: followup, next Q, or end."""
    q_count = ss("question_count")
    max_qs  = ss("max_questions")

    if q_count >= max_qs:
        end_interview()
    else:
        ask_next_question()


def handle_user_answer(answer: str):
    if not answer.strip():
        return

    add_message("user", answer, {"type": "answer"})

    q_dict   = ss("current_question")
    score    = score_answer_heuristic(answer, q_dict)
    scores   = ss("scores")
    scores.append(score)
    set_ss("scores", scores)

    # Update per-category scores
    cat_scores = ss("category_scores")
    cat = q_dict.get("category", "unknown")
    if cat not in cat_scores:
        cat_scores[cat] = []
    cat_scores[cat].append(score)
    set_ss("category_scores", cat_scores)

    badge  = score_badge_html(score)
    hint   = _feedback_hint(score, q_dict)
    fb_msg = f"✅ Answer recorded. {badge}\n\n{hint}"
    add_message("system", fb_msg, {"type": "feedback", "score": score})

    # Decide: if not already awaiting followup, ask one on first answer
    if not ss("awaiting_followup"):
        scalar = _to_scalar_score(score)
        # Only ask follow-up for non-trivial answers and not on final question
        if scalar is not None and scalar > 20 and ss("question_count") < ss("max_questions"):
            ask_followup(answer)
            return

    _maybe_advance()


def _feedback_hint(score: float, q_dict: dict) -> str:
    difficulty = q_dict.get("difficulty", "medium")
    if score >= 80:
        return "🌟 Strong answer! You demonstrated clear technical depth."
    if score >= 60:
        return "👍 Good answer. Consider adding more concrete examples or metrics."
    if score >= 40:
        tips = {
            "easy":   "Try to structure your answer with a clear explanation and an example.",
            "medium": "Aim for more specificity — name tools, metrics, or tradeoffs.",
            "hard":   "For hard questions, show you understand the tradeoffs, not just the definition.",
        }
        return f"💡 {tips.get(difficulty, 'Add more depth and specific details.')}"
    return "📚 Review this topic. Focus on the core concept, then add a real-world example."


def end_interview():
    set_ss("interview_complete", True)
    scores      = ss("scores")
    cat_scores  = ss("category_scores")
    role        = ss("role")

    avg = sum(scores) / len(scores) if scores else 0
    set_ss("total_score", avg)

    # Build summary
    lines = [
        f"## 🏁 Interview Complete — {role}",
        f"\n**Overall Score: {avg:.1f}/100** — {score_to_label(avg)}",
        f"\n**Questions answered:** {len(scores)}",
        "\n---",
        "\n### 📊 Category Breakdown",
    ]

    for cat in CANONICAL_CATEGORIES:
        if cat in cat_scores and cat_scores[cat]:
            cat_avg = sum(cat_scores[cat]) / len(cat_scores[cat])
            label   = CATEGORY_LABELS.get(cat, cat)
            bar_len = int(cat_avg / 10)
            bar     = "█" * bar_len + "░" * (10 - bar_len)
            lines.append(f"\n- **{label}**: {bar} {cat_avg:.0f}/100")

    lines.append("\n---")
    lines.append("\n### 🎯 Key Takeaways")

    if avg >= 75:
        lines.append("\n✅ You performed strongly across the board. Focus on the lower-scoring categories to reach the next level.")
    elif avg >= 55:
        lines.append("\n📈 Solid performance. Deepen your knowledge in the weaker categories and practice articulating tradeoffs.")
    else:
        lines.append("\n📚 There's significant room to grow. Review fundamentals in each category and practice structured answers (STAR for behavioral, concrete examples for technical).")

    # Weakest category advice
    if cat_scores:
        weakest_cat = min(cat_scores, key=lambda c: sum(cat_scores[c]) / len(cat_scores[c]))
        weakest_label = CATEGORY_LABELS.get(weakest_cat, weakest_cat)
        lines.append(f"\n💡 **Focus area:** {weakest_label} — spend extra prep time here.")

    lines.append(f"\n\n*Use the sidebar to restart and improve your score!*")

    summary = "".join(lines)
    add_message("assistant", summary, {"type": "summary"})


# ── Message Helpers ────────────────────────────────────────────────────────────
def add_message(role: str, content: str, meta: dict = None):
    messages = ss("messages")
    messages.append({"role": role, "content": content, "meta": meta or {}})
    set_ss("messages", messages)


# ── Chat Rendering ─────────────────────────────────────────────────────────────
def render_messages():
    messages = ss("messages")
    for msg in messages:
        role    = msg["role"]
        content = msg["content"]
        meta    = msg.get("meta", {})

        if role == "assistant":
            css_class = "chat-ai"
            icon      = "🤖"
        elif role == "user":
            css_class = "chat-user"
            icon      = "👤"
        else:
            css_class = "chat-system"
            icon      = "ℹ️"

        # Render markdown content properly
        st.markdown(
            f'<div class="{css_class}">{icon} {_md_to_html(content)}</div>',
            unsafe_allow_html=True,
        )


def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML for inline rendering in custom divs."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Newlines
    text = text.replace('\n\n', '<br><br>').replace('\n', '<br>')
    # Bullet lists
    text = re.sub(r'- (.+?)(<br>|$)', r'• \1<br>', text)
    return text


# ── Main UI ────────────────────────────────────────────────────────────────────
def main():
    render_sidebar()

    # ── Header ────────────────────────────────────────────────────────────────
    role = ss("role")
    st.markdown(f"# 🎯 AI Interview Coach")
    st.markdown(f"**Role:** {role} &nbsp;|&nbsp; **Mode:** Adaptive Difficulty &nbsp;|&nbsp; **Questions:** {ss('max_questions')}")
    st.markdown("---")

    # ── Welcome / Not Started ─────────────────────────────────────────────────
    if not ss("interview_started"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            ### Welcome to AI Interview Coach

            You've selected the **{role}** role.

            **What to expect:**
            - {ss('max_questions')} adaptive questions across 7 categories
            - Follow-up questions based on your answers
            - Real-time scoring and feedback
            - Detailed performance breakdown at the end

            **Tips for a great session:**
            - Answer like you're in a real interview
            - Use specific examples, metrics, and tradeoffs
            - Longer, structured answers score higher

            Click **▶️ Start Interview** in the sidebar to begin.
            """)
            if st.button("▶️ Start Interview", type="primary", use_container_width=True):
                start_interview()
                st.rerun()
        return

    # ── Chat history ──────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        render_messages()

    st.markdown("---")

    # ── Answer input ──────────────────────────────────────────────────────────
    if ss("interview_started") and not ss("interview_complete"):
        q_count = ss("question_count")
        max_qs  = ss("max_questions")
        awaiting_fu = ss("awaiting_followup")

        placeholder = (
            "Type your follow-up answer here..." if awaiting_fu
            else "Type your answer here. Be specific — use examples, metrics, and explain your reasoning..."
        )

        with st.form(key="answer_form", clear_on_submit=True):
            answer = st.text_area(
                "Your Answer",
                height=140,
                placeholder=placeholder,
                label_visibility="collapsed",
                key="answer_input",
            )
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                submitted = st.form_submit_button(
                    "📨 Submit Answer",
                    type="primary",
                    use_container_width=True,
                )
            with col2:
                skipped = st.form_submit_button(
                    "⏭️ Skip",
                    use_container_width=True,
                )
            with col3:
                progress_pct = q_count / max_qs if max_qs > 0 else 0
                st.markdown(
                    f"<div style='padding-top:8px;text-align:center;color:#aaa;font-size:0.85rem'>"
                    f"Q{q_count}/{max_qs}</div>",
                    unsafe_allow_html=True,
                )

            if submitted and answer.strip():
                handle_user_answer(answer.strip())
                st.rerun()
            elif skipped:
                skip_question()
                st.rerun()

        # Progress bar
        progress = q_count / max_qs if max_qs > 0 else 0
        st.progress(progress)
        st.caption(f"Question {q_count} of {max_qs} · {'Follow-up pending' if awaiting_fu else 'Main question'}")

    # ── Interview complete ─────────────────────────────────────────────────────
    elif ss("interview_complete"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start New Interview (Same Role)", use_container_width=True, type="primary"):
                reset_interview(keep_role=True)
                st.rerun()
        with col2:
            if st.button("🎭 Change Role & Restart", use_container_width=True):
                reset_interview(keep_role=False)
                st.rerun()


if __name__ == "__main__":
    main()
