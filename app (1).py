# app.py
# AI Interview Coach — Streamlit UI
# Run: streamlit run app.py

import streamlit as st

import plotly.graph_objects as go

from utils import init_session, reset_session, get_session, set_session, score_color, probability_color
from interview_engine import generate_question, generate_followup, get_opening_message
from evaluation import evaluate_answer, format_evaluation, answer_composite_score
from scoring import calculate_score
from resume_parser import parse_resume, resume_context_for_prompt

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #f8fafc; }

.card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

.question-card {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: white !important;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    font-size: 1.1rem;
    font-weight: 500;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(37,99,235,0.3);
}

.answer-card {
    background: #f0fdf4;
    border-left: 4px solid #10b981;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin-bottom: 12px;
    color: #065f46;
}

.score-hero {
    text-align: center;
    padding: 32px 16px;
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    border-radius: 16px;
    color: white;
    margin-bottom: 24px;
}

.score-big {
    font-size: 4.5rem;
    font-weight: 800;
    line-height: 1;
}

.prob-badge {
    display: inline-block;
    padding: 6px 20px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 1rem;
    margin-top: 10px;
}

.prob-high { background: #dcfce7; color: #15803d; }
.prob-medium { background: #fef9c3; color: #a16207; }
.prob-low { background: #fee2e2; color: #dc2626; }

.weakness-item {
    background: #fff7ed;
    border-left: 3px solid #f97316;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.9rem;
    color: #7c2d12;
}

.strength-item {
    background: #f0fdf4;
    border-left: 3px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.9rem;
    color: #064e3b;
}

.plan-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 8px 0;
}

.plan-area { font-weight: 700; color: #1e3a5f; font-size: 0.95rem; }
.plan-action { color: #374151; margin: 4px 0; font-size: 0.9rem; }
.plan-timeline { color: #6b7280; font-size: 0.8rem; }

.phase-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
    margin-bottom: 8px;
}

.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}

.stButton > button:first-child {
    background: linear-gradient(135deg, #1e3a5f, #2563eb) !important;
    color: white !important;
    border: none !important;
}

.stTextArea > div > textarea {
    border-radius: 8px !important;
    border: 1.5px solid #d1d5db !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
}

.stSelectbox > div { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session Init ──────────────────────────────────────────────────────────────
init_session()

# Ensure phase always has a safe default after init
if get_session("phase") is None:
    set_session("phase", "setup")


# ─── Helper: Finalize Interview ────────────────────────────────────────────────
# Must be defined BEFORE the sidebar so it can be called from sidebar buttons.

def _do_final_scoring():
    evals = get_session("feedbacks")
    role = get_session("role")
    with st.spinner("Computing final score..."):
        score_data = calculate_score(evals, role)
        set_session("final_score", score_data)
        set_session("phase", "results")


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 AI Interview Coach")
    st.markdown("---")

    # Read phase fresh on every rerun with safe fallback
    phase = get_session("phase") or "setup"

    if phase == "setup":
        st.markdown("### Interview Setup")

        # Widget values are stored directly in st.session_state via their key.
        # We read them back inside the button handler — never call set_session
        # on every render, which would overwrite state mid-rerun.
        st.selectbox(
            "Target Role",
            ["Data Scientist", "Software Engineer (SDE)", "ML Engineer", "Product Manager", "Data Analyst"],
            key="role_select",
        )
        st.markdown("### Resume (Optional)")
        st.text_area(
            "Paste resume text for personalized questions",
            height=220,
            placeholder="Senior Data Scientist with 4 years experience...\nSkills: Python, TensorFlow, Spark...\nProjects: Built churn prediction model...",
            key="resume_input",
        )
        st.markdown("---")
        st.slider("Number of Questions", min_value=3, max_value=7, value=5, key="max_q_slider")

        st.markdown("---")
        if st.button("🚀 Start Interview", use_container_width=True):
            # Read current widget values directly from session_state by key
            _role = st.session_state.get("role_select", "Data Scientist")
            _resume = st.session_state.get("resume_input", "")
            _max_q = st.session_state.get("max_q_slider", 5)

            # Persist into our named session keys
            set_session("role", _role)
            set_session("resume_text", _resume)
            set_session("max_questions", _max_q)

            with st.spinner("Preparing your interview..."):
                # Parse resume if provided
                if _resume.strip():
                    parsed = parse_resume(_resume)
                    set_session("parsed_resume", parsed)

                # Generate first question
                resume_ctx = resume_context_for_prompt(get_session("parsed_resume"))
                first_q = generate_question(_role, resume_ctx, [])
                set_session("current_question", first_q)
                set_session("questions", [first_q])
                set_session("answers", [])
                set_session("feedbacks", [])
                set_session("phase", "interview")
                set_session("awaiting_answer", True)
            st.rerun()

    elif phase == "interview":
        q_asked = len(get_session("answers"))
        max_q = get_session("max_questions")
        progress_val = q_asked / max_q if max_q > 0 else 0
        st.markdown("### Progress")
        st.progress(progress_val, text=f"{q_asked}/{max_q} answered")

        evals = get_session("feedbacks")
        if evals:
            scores = [answer_composite_score(e) for e in evals]
            avg = sum(scores) / len(scores)
            color = score_color(avg)
            st.markdown(f"**Running Score:** <span style='color:{color};font-weight:700;'>{avg:.0f}/100</span>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("⚡ End & Get Score", use_container_width=True):
            _do_final_scoring()
            st.rerun()

    elif phase == "results":
        st.markdown("### Session Complete")
        score_data = get_session("final_score")
        if score_data:
            fs = score_data["final_score"]
            color = score_color(fs)
            st.markdown(f"**Final Score:** <span style='color:{color};font-weight:800;font-size:1.4rem;'>{fs}/100</span>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🔄 New Interview", use_container_width=True):
            reset_session()
            st.rerun()


# ─── Main Content ──────────────────────────────────────────────────────────────
phase = get_session("phase") or "setup"

# ══════════════════════════════════════════════════════════════════════════════
# PHASE: SETUP
# ══════════════════════════════════════════════════════════════════════════════
if phase == "setup":
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 48px 0 32px;">
            <div style="font-size:3.5rem; margin-bottom:12px;">🎯</div>
            <h1 style="font-size:2.4rem; font-weight:800; color:#1e3a5f; margin-bottom:8px;">
                AI Interview Coach
            </h1>
            <p style="color:#64748b; font-size:1.1rem; max-width:480px; margin:0 auto 36px;">
                Practice role-specific mock interviews, get instant answer evaluation, 
                and receive a final score with your personalized improvement plan.
            </p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        features = [
            ("💬", "Smart Interviewer", "Role-specific questions with intelligent follow-ups"),
            ("📊", "Answer Scoring", "Clarity · Technical · Communication · Confidence"),
            ("📋", "Final Report", "Score, selection probability & 30-day action plan"),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3], features):
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center; min-height:130px;">
                    <div style="font-size:1.8rem;">{icon}</div>
                    <div style="font-weight:700; color:#1e3a5f; margin:6px 0 4px;">{title}</div>
                    <div style="font-size:0.82rem; color:#64748b;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <p style="text-align:center; color:#94a3b8; font-size:0.9rem; margin-top:24px;">
            ← Configure your role and resume in the sidebar, then click <strong>Start Interview</strong>
        </p>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "interview":
    role = get_session("role")
    # Always work on list COPIES so that .append() + set_session persists correctly.
    questions = list(get_session("questions") or [])
    answers = list(get_session("answers") or [])
    feedbacks = list(get_session("feedbacks") or [])
    current_question = get_session("current_question") or ""
    max_q = get_session("max_questions") or 5

    st.markdown(f'<span class="phase-badge">🎙 LIVE INTERVIEW — {role}</span>', unsafe_allow_html=True)
    st.markdown(f"## Question {len(answers) + 1} of {max_q}")

    # ── Current question ──
    if current_question:
        st.markdown(f'<div class="question-card">🤖 {current_question}</div>', unsafe_allow_html=True)
    else:
        st.warning("No question loaded. Please restart the interview.")

    # ── Answer input ──
    st.markdown("**Your Answer:**")
    answer_input = st.text_area(
        "Answer",
        height=150,
        placeholder="Take a moment to think, then type your answer here. Be specific — use examples and concrete outcomes.",
        label_visibility="collapsed",
        key=f"answer_{len(answers)}",
    )

    col_submit, col_skip = st.columns([3, 1])
    with col_submit:
        submit = st.button("✅ Submit Answer", use_container_width=True)
    with col_skip:
        skip = st.button("⏭ Skip", use_container_width=True)

    if submit and answer_input.strip():
        with st.spinner("Evaluating your answer..."):
            ev = evaluate_answer(answer_input, current_question, role)
            answers.append(answer_input)
            feedbacks.append(ev)
            set_session("answers", answers)
            set_session("feedbacks", feedbacks)

        # Show evaluation immediately before rerun
        with st.expander("📋 Answer Evaluation", expanded=True):
            st.markdown(format_evaluation(ev))

        if len(answers) >= max_q:
            _do_final_scoring()
            st.rerun()
        else:
            with st.spinner("Preparing next question..."):
                resume_ctx = resume_context_for_prompt(get_session("parsed_resume"))
                next_q = generate_question(role, resume_ctx, questions)
                questions.append(next_q)
                set_session("questions", questions)
                set_session("current_question", next_q)
            st.rerun()

    elif skip:
        answers.append("[Skipped]")
        feedbacks.append({
            "clarity": 0, "technical": 0, "communication": 0, "confidence": 0,
            "feedback": "Question skipped.",
            "improved_answer": "",
            "question": current_question,
            "answer": "[Skipped]",
        })
        set_session("answers", answers)
        set_session("feedbacks", feedbacks)

        if len(answers) >= max_q:
            _do_final_scoring()
            st.rerun()
        else:
            resume_ctx = resume_context_for_prompt(get_session("parsed_resume"))
            next_q = generate_question(role, resume_ctx, questions)
            questions.append(next_q)
            set_session("questions", questions)
            set_session("current_question", next_q)
            st.rerun()

    # ── Previous Q&A History ──
    if answers:
        st.markdown("---")
        st.markdown("### Previous Questions & Feedback")
        # questions[:-1] aligns with the answered questions list
        prev_questions = questions[:-1] if len(questions) > len(answers) else questions
        for i, (q, a, ev) in enumerate(zip(prev_questions, answers, feedbacks), 1):
            composite = answer_composite_score(ev)
            color = score_color(composite)
            label = q[:60] + "..." if len(q) > 60 else q
            with st.expander(f"Q{i} — Score: {composite:.0f}/100 — {label}"):
                st.markdown(f'<div class="question-card" style="font-size:0.95rem; padding:14px 18px;">{q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-card">👤 {a}</div>', unsafe_allow_html=True)
                st.markdown(format_evaluation(ev))


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "results":
    score_data = get_session("final_score")
    role = get_session("role")

    if not score_data:
        st.error("No score data. Please complete an interview first.")
        st.stop()

    fs = score_data["final_score"]
    prob = score_data["probability"]
    prob_icon = score_data.get("probability_icon", "")
    prob_note = score_data.get("probability_note", "")
    dim_scores = score_data.get("dimension_scores", {})
    per_answer = score_data.get("per_answer_scores", [])
    strengths = score_data.get("strengths", [])
    weaknesses = score_data.get("weaknesses", [])
    plan = score_data.get("improvement_plan", [])

    prob_class = f"prob-{prob.lower()}"

    # ── Score Hero ──
    st.markdown(f"""
    <div class="score-hero">
        <div style="font-size:0.85rem; font-weight:600; opacity:0.8; letter-spacing:2px; text-transform:uppercase; margin-bottom:8px;">
            {role} Interview Complete
        </div>
        <div class="score-big">{fs}<span style="font-size:2rem;opacity:0.6;">/100</span></div>
        <div style="margin-top:12px;">
            <span class="prob-badge {prob_class}">{prob_icon} {prob} Selection Probability</span>
        </div>
        <div style="margin-top:8px; opacity:0.75; font-size:0.9rem;">{prob_note}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Dimension Scores + Charts ──
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📊 Skill Breakdown")

        # Radar chart
        if dim_scores:
            cats = ["Technical", "Communication", "Confidence", "Clarity"]
            vals = [
                dim_scores.get("technical", 0),
                dim_scores.get("communication", 0),
                dim_scores.get("confidence", 0),
                dim_scores.get("clarity", 0),
            ]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(37,99,235,0.15)",
                line=dict(color="#2563eb", width=2.5),
                name="Your Score",
            ))
            fig.add_trace(go.Scatterpolar(
                r=[70, 70, 70, 70, 70],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(16,185,129,0.05)",
                line=dict(color="#10b981", width=1.5, dash="dot"),
                name="Target (70)",
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
                ),
                showlegend=True,
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="white",
                font=dict(family="DM Sans"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📈 Answer Progression")

        if per_answer:
            q_labels = [f"Q{i+1}" for i in range(len(per_answer))]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=q_labels,
                y=per_answer,
                mode="lines+markers",
                line=dict(color="#2563eb", width=3),
                marker=dict(size=10, color="#2563eb", line=dict(color="white", width=2)),
                fill="tozeroy",
                fillcolor="rgba(37,99,235,0.08)",
                name="Answer Score",
            ))
            fig2.add_hline(y=70, line_dash="dot", line_color="#10b981",
                           annotation_text="Target: 70", annotation_position="top right")
            fig2.update_layout(
                xaxis=dict(title="Question", gridcolor="#f1f5f9"),
                yaxis=dict(title="Score (0-100)", range=[0, 105], gridcolor="#f1f5f9"),
                height=320,
                margin=dict(l=20, r=20, t=20, b=40),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(family="DM Sans"),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Strengths & Weaknesses ──
    st.markdown("---")
    col_s, col_w = st.columns(2)

    with col_s:
        st.markdown("### ✅ Strengths")
        if strengths:
            for s in strengths:
                st.markdown(f'<div class="strength-item">💚 {s}</div>', unsafe_allow_html=True)
        else:
            st.info("Keep practicing to build identifiable strengths.")

    with col_w:
        st.markdown("### ⚠️ Weaknesses")
        if weaknesses:
            for w in weaknesses:
                st.markdown(f'<div class="weakness-item">🔸 {w}</div>', unsafe_allow_html=True)
        else:
            st.success("No major weaknesses detected!")

    # ── Improvement Plan ──
    st.markdown("---")
    st.markdown("### 🗺️ 30-Day Improvement Plan")

    if plan:
        for i, item in enumerate(plan, 1):
            area = item.get("area", "")
            action = item.get("action", "")
            timeline = item.get("timeline", "")
            st.markdown(f"""
            <div class="plan-item">
                <div class="plan-area">Step {i}: {area}</div>
                <div class="plan-action">→ {action}</div>
                <div class="plan-timeline">⏱ Timeline: {timeline}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Complete more questions to generate a personalized plan.")

    # ── Full Q&A Transcript ──
    st.markdown("---")
    questions = get_session("questions")
    answers = get_session("answers")
    feedbacks_list = get_session("feedbacks")

    with st.expander("📜 Full Interview Transcript & Feedback", expanded=False):
        for i, (q, a, ev) in enumerate(zip(questions, answers, feedbacks_list), 1):
            composite = answer_composite_score(ev)
            st.markdown(f"#### Q{i} — Score: {composite:.0f}/100")
            st.markdown(f'<div class="question-card" style="font-size:0.9rem; padding:12px 16px;">{q}</div>', unsafe_allow_html=True)
            if a != "[Skipped]":
                st.markdown(f'<div class="answer-card">👤 {a}</div>', unsafe_allow_html=True)
            st.markdown(format_evaluation(ev))
            st.markdown("---")
