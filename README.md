# 🎯 AI Interview Coach

A complete, modular AI-powered mock interview system built with Streamlit and Claude.

---

## Project Overview

| Module | Purpose |
|---|---|
| `app.py` | Streamlit UI: chat interface, score dashboard, results page |
| `interview_engine.py` | Question generation, follow-ups, fallback question bank |
| `evaluation.py` | Per-answer scoring (Clarity, Technical, Communication, Confidence) |
| `scoring.py` | Final weighted score, selection probability, improvement plan |
| `resume_parser.py` | Extract skills/projects from resume text (regex + LLM) |
| `prompts.py` | All LLM prompt templates in one place |
| `utils.py` | API client, JSON parser, session helpers |

---

## Setup & Installation

### 1. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key

**Option A — Environment variable (recommended):**
```bash
export ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"   # macOS/Linux
set ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE         # Windows CMD
```

**Option B — .env file:**
```bash
echo "ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE" > .env
```

**Option C — Streamlit secrets:**
```bash
mkdir -p .streamlit
echo 'ANTHROPIC_API_KEY = "sk-ant-YOUR_KEY_HERE"' > .streamlit/secrets.toml
```

### 4. Run the app
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## How to Use

1. **Configure** — Select your target role (Data Scientist, SDE, ML Engineer, PM, Data Analyst) in the sidebar
2. **Resume** — Optionally paste resume text for personalized questions
3. **Start** — Click "Start Interview" to begin
4. **Answer** — Read each question, type your answer, click Submit
5. **Feedback** — Get instant scoring after each answer
6. **Results** — After all questions, view your final score, radar chart, and improvement plan

---

## Scoring System

```
Final Score (0-100) =
    Technical Accuracy  × 30%
  + Communication       × 25%
  + Clarity             × 25%
  + Confidence          × 20%

Selection Probability:
  80–100 → High   🟢  (Strong candidate)
  60–79  → Medium 🟡  (Competitive, needs polish)
  0–59   → Low    🔴  (Needs more preparation)
```

---

## Example API Usage

```python
from evaluation import evaluate_answer
from scoring import calculate_score

# Evaluate a single answer
ev = evaluate_answer(
    answer="I used SMOTE to handle the 95/5 class imbalance, then tuned threshold...",
    question="How do you handle class imbalance in a classification problem?",
    role="Data Scientist"
)
print(ev["technical"])     # 8
print(ev["feedback"])      # "Strong technical depth..."

# Calculate final score from all evaluations
score = calculate_score([ev1, ev2, ev3, ev4, ev5], role="Data Scientist")
print(score["final_score"])     # 74
print(score["probability"])     # "Medium"
print(score["weaknesses"])      # ["Answer structure...", ...]
```

---

## Customization

| What | Where |
|---|---|
| Add roles | `FALLBACK_QUESTIONS` in `interview_engine.py` |
| Change scoring weights | `WEIGHTS` in `scoring.py` |
| Edit prompts | `prompts.py` |
| Change question count | Sidebar slider in `app.py` |
| Add evaluation dimensions | `evaluation.py` + `EVALUATION_PROMPT` in `prompts.py` |

---

## Requirements

- Python 3.9+
- Anthropic API key (get one at console.anthropic.com)
- Internet connection for LLM calls
