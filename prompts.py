# prompts.py
# All LLM prompt templates for the AI Interview Coach

QUESTION_PROMPT = """You are a senior technical interviewer at a top tech company.
Generate ONE interview question for a {role} candidate.

Resume context:
{resume_text}

Previously asked questions (do not repeat):
{previous_questions}

Rules:
- Ask exactly ONE question
- Make it specific to the role and resume if resume is provided
- Vary between: technical concepts, system design, behavioral, and problem-solving
- Keep it concise and clear
- Do NOT include numbering or prefixes like "Question:"

Return only the question text, nothing else."""


FOLLOWUP_PROMPT = """You are a technical interviewer. The candidate answered:

Question: {question}
Answer: {answer}

Generate ONE sharp follow-up question that:
- Probes deeper into their answer
- Challenges an assumption or asks for specifics
- Is directly relevant to what they said

Return only the follow-up question, nothing else."""


EVALUATION_PROMPT = """You are an expert technical interview evaluator.

Role: {role}
Question: {question}
Candidate Answer: {answer}

Evaluate this answer and return ONLY a valid JSON object with this exact structure:
{{
  "clarity": <integer 0-10>,
  "technical": <integer 0-10>,
  "communication": <integer 0-10>,
  "confidence": <integer 0-10>,
  "feedback": "<2-3 sentences of honest, specific feedback>",
  "improved_answer": "<A model answer in 3-5 sentences showing what an ideal response looks like>"
}}

Scoring guide:
- clarity (0-10): How well-structured and easy to follow was the answer?
- technical (0-10): Were facts, methods, and concepts correct and appropriately deep?
- communication (0-10): Professional tone, concise language, avoided excessive filler?
- confidence (0-10): Did they own their answer? Excessive hedging reduces this score.

Be honest. Most answers deserve 4-7. Only exceptional answers get 8-10.
Return ONLY the JSON object. No markdown, no explanation, no preamble."""


FINAL_SCORING_PROMPT = """You are a senior hiring manager evaluating a complete interview.

Role: {role}
Number of questions answered: {num_answers}

Evaluation scores per answer:
{scores_summary}

Based on these scores, return ONLY a valid JSON object:
{{
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
  "improvement_plan": [
    {{"area": "<skill>", "action": "<specific action>", "timeline": "<1-2 weeks / 1 month>"}},
    {{"area": "<skill>", "action": "<specific action>", "timeline": "<1-2 weeks / 1 month>"}},
    {{"area": "<skill>", "action": "<specific action>", "timeline": "<1-2 weeks / 1 month>"}}
  ]
}}

Base strengths/weaknesses on actual score patterns. Be specific and actionable.
Return ONLY the JSON object."""


RESUME_EXTRACTION_PROMPT = """Extract key information from this resume text.

Resume:
{resume_text}

Return ONLY a valid JSON object:
{{
  "skills": ["skill1", "skill2", "skill3"],
  "projects": ["project description 1", "project description 2"],
  "experience_years": <integer or 0 if unclear>,
  "key_technologies": ["tech1", "tech2", "tech3"]
}}

Return ONLY the JSON object."""
