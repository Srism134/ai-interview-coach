# interview_engine.py
# Generates interview questions using rule-based banks. Fully offline — no API.

import random
import re

# ── Question Banks ─────────────────────────────────────────────────────────────
# Each role has categorised sub-banks so questions stay varied across dimensions.

QUESTION_BANK = {
    "Data Scientist": {
        "ml_fundamentals": [
            "Explain the bias-variance tradeoff and how it affects model selection.",
            "What is regularisation and when would you choose L1 over L2?",
            "Walk me through how gradient descent works and its variants (SGD, Adam, RMSProp).",
            "How does a Random Forest differ from Gradient Boosting? When would you use each?",
            "Explain how cross-validation works and why k-fold is preferred over a single train/test split.",
            "What is the curse of dimensionality and how do you mitigate it?",
            "Describe how a decision tree chooses its splits. What metrics does it use?",
            "What is the difference between bagging and boosting?",
            "Explain what precision, recall, and F1-score measure and when each matters more.",
            "What is ROC-AUC and what does a curve below 0.5 mean?",
        ],
        "statistics": [
            "What is the Central Limit Theorem and why is it important in practice?",
            "Explain p-values and confidence intervals — what do they actually tell you?",
            "How would you design an A/B test for a new recommendation feature?",
            "What is the difference between correlation and causation? Give a concrete example.",
            "How do you handle multicollinearity in a regression model?",
            "Explain Bayesian vs frequentist statistics. When would you use each?",
            "What is a Type I vs Type II error and how do you balance them?",
            "How do you determine the required sample size for an experiment?",
            "What statistical tests would you use to compare two groups? Walk me through your decision process.",
            "Explain what heteroscedasticity is and how you'd detect it.",
        ],
        "data_engineering": [
            "How do you handle missing data? Walk me through your decision process.",
            "What is your approach to feature selection for a high-dimensional dataset?",
            "How do you handle class imbalance in a classification problem?",
            "Walk me through a full feature engineering pipeline you've built.",
            "How would you detect and handle outliers in a dataset?",
            "What is data leakage and how do you prevent it?",
            "How do you validate that your model is learning signal, not noise?",
            "Explain the difference between normalisation and standardisation. When does it matter?",
        ],
        "applied": [
            "Walk me through a machine learning project you've built end-to-end.",
            "Describe a time your analysis directly changed a business decision.",
            "How do you explain a complex model's output to a non-technical stakeholder?",
            "Tell me about a time a model performed well in development but poorly in production.",
            "How do you decide when a machine learning solution is overkill?",
            "Walk me through how you would build a churn prediction model from scratch.",
            "How would you approach building a recommendation system for an e-commerce site?",
        ],
    },

    "Software Engineer (SDE)": {
        "data_structures_algorithms": [
            "Explain the difference between a stack and a queue. When would you use each?",
            "Walk me through how a hash table works, including collision resolution strategies.",
            "What is the time and space complexity of quicksort? What are its best/worst cases?",
            "When would you use a graph over a tree data structure?",
            "Explain dynamic programming. Give an example of a problem it solves well.",
            "What is the difference between BFS and DFS? When is each appropriate?",
            "How does a binary search tree differ from a balanced BST like an AVL tree?",
            "Explain what a heap is and give a real use case for a min-heap.",
            "What is the difference between O(n log n) and O(n²) in practice at scale?",
            "How would you detect a cycle in a linked list?",
        ],
        "system_design": [
            "Describe the most complex system you've designed or significantly contributed to.",
            "How would you design a URL shortener like bit.ly?",
            "Explain the CAP theorem and give a real-world tradeoff example.",
            "How do you decide when to use a cache and when not to?",
            "Walk me through how you would design a rate limiter.",
            "How would you design a notification service that handles millions of users?",
            "Explain the difference between SQL and NoSQL databases. When would you choose each?",
            "How do you approach horizontal vs vertical scaling?",
            "What is a message queue and when would you introduce one into an architecture?",
            "How would you design a system to handle 100x traffic spikes?",
        ],
        "software_craft": [
            "How do you approach debugging a production incident under pressure?",
            "Walk me through your approach to writing a code review.",
            "How do you ensure your code is maintainable for the next engineer?",
            "Describe a time you had to refactor critical code under time pressure.",
            "How do you decide when to rewrite vs refactor a piece of code?",
            "What does good test coverage mean to you? How do you decide what to test?",
            "Explain SOLID principles. Which do you find hardest to apply consistently?",
            "How do you manage technical debt in a fast-moving team?",
        ],
        "applied": [
            "Tell me about the most challenging bug you've ever tracked down.",
            "Describe a time you disagreed with a technical decision and what you did.",
            "How do you onboard yourself to a large, unfamiliar codebase?",
            "Tell me about a system you built that failed and what you learned.",
            "How do you balance shipping fast with maintaining code quality?",
        ],
    },

    "ML Engineer": {
        "mlops": [
            "How do you take a trained model from a notebook to production?",
            "What is your strategy for detecting and handling model drift?",
            "Describe how you would design a feature store from scratch.",
            "Walk me through your ML pipeline monitoring setup.",
            "How do you handle training/serving skew?",
            "What CI/CD practices apply specifically to ML pipelines?",
            "How do you version datasets and models in a reproducible way?",
            "What is shadow deployment and when would you use it for a new model?",
            "How do you roll back a bad model in production safely?",
            "Describe your approach to A/B testing two model versions in production.",
        ],
        "infrastructure": [
            "How do you optimise model inference latency without sacrificing accuracy?",
            "Explain the tradeoffs between batch inference and real-time inference.",
            "How would you build a scalable data ingestion pipeline for training?",
            "What is model quantisation and when is it appropriate?",
            "How do you containerise and deploy an ML model with Docker and Kubernetes?",
            "Explain the role of a model registry in an MLOps workflow.",
            "How do you manage compute costs for large-scale model training?",
            "What tools have you used for experiment tracking and why?",
        ],
        "ml_fundamentals": [
            "Explain the bias-variance tradeoff in the context of production ML systems.",
            "How do you handle class imbalance for a model that serves live traffic?",
            "What is transfer learning and when does it save you significant effort?",
            "Walk me through how you would choose between fine-tuning and training from scratch.",
            "How do you evaluate a model's fairness across demographic groups?",
            "Explain regularisation and when it matters most in production models.",
        ],
        "applied": [
            "Describe a production ML incident you dealt with and how you resolved it.",
            "Tell me about the most complex ML system you've shipped end-to-end.",
            "How do you communicate model performance to a non-technical product team?",
            "Walk me through a time you had to debug a model that worked in dev but failed in prod.",
            "How do you prioritise which models to maintain vs deprecate?",
        ],
    },

    "Product Manager": {
        "strategy": [
            "How do you prioritise features when resources are constrained?",
            "Walk me through a product you took from 0 to 1.",
            "How do you identify the right problem to solve before building anything?",
            "How do you decide whether to build, buy, or partner for a capability?",
            "Describe how you would respond to a major competitor launching a similar feature.",
            "How do you define and defend your product's north star metric?",
            "How do you balance short-term user requests with long-term product vision?",
        ],
        "execution": [
            "How do you measure the success of a feature after launch?",
            "Describe how you'd handle a major unexplained drop in a key metric.",
            "How do you align engineering, design, and business on a roadmap?",
            "Walk me through how you write a product requirements document.",
            "How do you manage scope creep on a project with a fixed deadline?",
            "How do you decide when a feature is good enough to ship?",
        ],
        "applied": [
            "Tell me about a product decision you made that turned out to be wrong.",
            "How do you handle pushback from engineering on your priorities?",
            "Describe the most difficult stakeholder situation you've navigated.",
            "How do you gather and validate user insights before committing to a feature?",
            "Tell me about a time you had to kill a feature or project mid-stream.",
        ],
    },

    "Data Analyst": {
        "sql_data": [
            "Walk me through the most complex SQL query you've written and why it was needed.",
            "How do you validate data quality before running an analysis?",
            "Explain the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
            "How do you handle conflicting data from two sources?",
            "What is a window function? Give a real example of when you'd use one.",
            "How do you approach exploratory data analysis on a dataset you've never seen?",
            "What does it mean for data to be 'tidy' and why does it matter?",
        ],
        "statistics_analysis": [
            "Walk me through a time your analysis changed a business decision.",
            "How do you detect and handle outliers in an analytical dataset?",
            "What is cohort analysis and when is it the right tool?",
            "How do you determine whether a metric change is statistically meaningful?",
            "Explain funnel analysis and how you'd diagnose a drop at a specific stage.",
            "What is the difference between a leading and a lagging indicator?",
        ],
        "communication": [
            "How do you communicate findings to a non-technical audience?",
            "Describe a time you had to push back on a stakeholder's interpretation of data.",
            "How do you decide what to include vs exclude from an analysis presentation?",
            "How do you visualise data to make a recommendation clear and defensible?",
            "Tell me about a time you caught an error in someone else's analysis.",
        ],
    },
}

# ── Resume Keyword → Sub-bank Mapping ─────────────────────────────────────────
# If resume contains these keywords, bias toward that sub-bank for variety.

RESUME_KEYWORD_MAP = {
    "Data Scientist": {
        "tensorflow keras pytorch deep learning neural": "ml_fundamentals",
        "experiment hypothesis ab test p-value statistics": "statistics",
        "spark hadoop pipeline etl feature engineering": "data_engineering",
        "stakeholder business dashboard reporting": "applied",
    },
    "Software Engineer (SDE)": {
        "leetcode algorithm competitive programming": "data_structures_algorithms",
        "microservice kubernetes docker aws cloud distributed": "system_design",
        "refactor review clean code solid tdd": "software_craft",
        "incident production oncall debugging": "applied",
    },
    "ML Engineer": {
        "mlflow kubeflow airflow pipeline deploy": "mlops",
        "kubernetes docker triton onnx serving inference": "infrastructure",
        "model training fine-tune transfer": "ml_fundamentals",
        "production incident rollback": "applied",
    },
    "Product Manager": {
        "roadmap strategy okr vision": "strategy",
        "sprint agile jira release": "execution",
        "user research customer interview": "applied",
    },
    "Data Analyst": {
        "sql postgres bigquery redshift dbt": "sql_data",
        "regression cohort funnel statistics": "statistics_analysis",
        "dashboard tableau looker powerbi stakeholder": "communication",
    },
}


# ── Core Public Functions ──────────────────────────────────────────────────────

def generate_question(role: str, resume_text: str = "", previous_questions: list = None) -> str:
    """
    Generate the next interview question for the given role.
    Fully offline — uses rule-based question banks with resume-aware sub-bank
    weighting to avoid repeats and keep questions varied.

    Args:
        role: Target job role.
        resume_text: Raw resume text (may be empty).
        previous_questions: List of already-asked questions to avoid repeats.

    Returns:
        A single question string.
    """
    if previous_questions is None:
        previous_questions = []

    # Normalise role key — fall back to closest match
    bank = QUESTION_BANK.get(role)
    if bank is None:
        # Try prefix match (e.g. "Software Engineer" → "Software Engineer (SDE)")
        for key in QUESTION_BANK:
            if role.lower() in key.lower() or key.lower() in role.lower():
                bank = QUESTION_BANK[key]
                role = key
                break
        if bank is None:
            bank = QUESTION_BANK["Data Scientist"]
            role = "Data Scientist"

    prev_lower = {q.strip().lower() for q in previous_questions}

    # Determine preferred sub-bank order based on resume keywords
    ordered_subbanks = _subbank_order(role, resume_text, list(bank.keys()))

    # Walk sub-banks in preferred order; pick first unused question
    for subbank_name in ordered_subbanks:
        questions = bank[subbank_name]
        # Shuffle within sub-bank for variety, but use deterministic seed
        # based on how many questions have been asked so prevent same Q each time
        candidates = [q for q in questions if q.strip().lower() not in prev_lower]
        if candidates:
            # Pick based on count so successive calls don't always return index 0
            idx = len(previous_questions) % len(candidates)
            return candidates[idx]

    # All questions exhausted — recycle from full bank, avoiding exact last asked
    last = previous_questions[-1].strip().lower() if previous_questions else ""
    all_qs = [q for sub in bank.values() for q in sub]
    recycled = [q for q in all_qs if q.strip().lower() != last]
    if recycled:
        return recycled[len(previous_questions) % len(recycled)]
    return all_qs[0]


def generate_followup(question: str, answer: str) -> str:
    """
    Generate a contextual follow-up question based on the candidate's answer.
    Fully offline — uses keyword detection and answer length heuristics.

    Args:
        question: The original interview question.
        answer: The candidate's answer.

    Returns:
        A follow-up question string.
    """
    if not answer or len(answer.strip()) < 10:
        return "Could you elaborate on that? What specific steps did you take?"

    answer_lower = answer.lower()
    question_lower = question.lower()

    # Keyword-triggered follow-ups (checked in priority order)
    triggers = [
        (["challenge", "difficult", "hard", "struggle", "problem"],
         "What was the most difficult part of that, and how did you specifically overcome it?"),
        (["team", "collaborate", "together", "stakeholder", "cross-functional"],
         "How did you handle disagreements or differing priorities within the team?"),
        (["result", "outcome", "impact", "improve", "increase", "decrease", "reduce"],
         "How did you measure the success of that outcome? What metrics did you track?"),
        (["model", "algorithm", "train", "accuracy", "performance"],
         "How did you validate that the model generalised well beyond your training data?"),
        (["deploy", "production", "ship", "launch", "release"],
         "What monitoring and rollback strategy did you put in place after deployment?"),
        (["data", "dataset", "pipeline", "etl", "ingest"],
         "What data quality issues did you encounter and how did you handle them?"),
        (["design", "architect", "system", "scale", "service"],
         "How did you account for failure modes and ensure the system remained resilient?"),
        (["decide", "decision", "chose", "choice", "trade-off", "tradeoff"],
         "Looking back, what would you do differently and why?"),
        (["fail", "wrong", "mistake", "didn't work", "issue", "bug"],
         "What did you learn from that experience and how have you applied it since?"),
        (["learn", "taught", "course", "read", "study"],
         "How have you applied that learning in a real project?"),
    ]

    for keywords, followup in triggers:
        if any(kw in answer_lower or kw in question_lower for kw in keywords):
            return followup

    # Length-based generic follow-ups — short answers get a depth probe
    word_count = len(answer.split())
    if word_count < 40:
        return "Can you go deeper on that? Walk me through the specific steps you took and the outcome."
    if word_count < 80:
        return "That's a good start — can you quantify the impact? What numbers or metrics back that up?"

    # Default rotation based on answer length for variety
    generic = [
        "What would you do differently if you faced this situation again?",
        "How did you communicate this to your team or stakeholders?",
        "What was the biggest risk in your approach, and how did you mitigate it?",
        "How did you prioritise when multiple things were competing for your attention?",
        "What did you learn from this that changed how you work?",
    ]
    return generic[word_count % len(generic)]


def get_opening_message(role: str) -> str:
    """Return a warm opening message to start the interview."""
    return (
        f"Welcome! I'll be your interviewer today for the **{role}** position. "
        f"We'll go through a series of questions — feel free to take a moment before answering. "
        f"Speak in as much detail as you can; specific examples and outcomes always help. "
        f"Ready? Let's begin with your first question."
    )


# ── Private Helpers ────────────────────────────────────────────────────────────

def _subbank_order(role: str, resume_text: str, all_subbanks: list) -> list:
    """
    Return sub-bank names ordered by relevance to resume keywords.
    Sub-banks with resume matches come first; rest follow in default order.
    """
    if not resume_text:
        return all_subbanks

    resume_lower = resume_text.lower()
    keyword_map = RESUME_KEYWORD_MAP.get(role, {})
    preferred = None

    for keyword_str, subbank in keyword_map.items():
        keywords = keyword_str.split()
        if any(kw in resume_lower for kw in keywords):
            preferred = subbank
            break

    if preferred and preferred in all_subbanks:
        ordered = [preferred] + [s for s in all_subbanks if s != preferred]
        return ordered

    return all_subbanks
