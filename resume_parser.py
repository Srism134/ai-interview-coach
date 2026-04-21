# resume_parser.py
# Extract skills, projects, and experience from resume text.
# Uses keyword/regex approach with optional LLM enhancement.

import re
from utils import call_llm, safe_parse_json
from prompts import RESUME_EXTRACTION_PROMPT

# ── Keyword Lists ──────────────────────────────────────────────────────────────

TECH_SKILLS = [
    # Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "go", "rust",
    "scala", "kotlin", "swift", "r", "matlab", "sql", "bash", "shell",
    # ML / DS
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost",
    "lightgbm", "catboost", "numpy", "pandas", "scipy", "matplotlib",
    "seaborn", "plotly", "hugging face", "transformers", "langchain",
    "openai", "llm", "nlp", "computer vision", "deep learning",
    "machine learning", "reinforcement learning", "mlops",
    # Data Engineering
    "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake", "databricks",
    "redshift", "bigquery", "hive", "presto", "flink",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite",
    # Cloud / Infra
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd",
    "github actions", "jenkins", "linux", "git",
    # Web
    "fastapi", "flask", "django", "react", "node.js", "rest", "graphql",
    "microservices", "api",
    # Concepts
    "a/b testing", "statistics", "data structures", "algorithms",
    "system design", "agile", "scrum",
]


# ── Regex-based Extraction ─────────────────────────────────────────────────────

def extract_skills_regex(text: str) -> list:
    """Extract tech skills via keyword matching (case-insensitive)."""
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        # Use word-boundary-aware matching
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill.title() if len(skill) > 3 else skill.upper())
    # Deduplicate preserving order
    seen = set()
    unique = []
    for s in found:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique[:20]  # Cap at 20 skills


def extract_projects_regex(text: str) -> list:
    """Extract project names/descriptions using common resume patterns."""
    projects = []

    # Pattern: lines after "Project", "Projects", "Personal Projects", etc.
    project_section = re.search(
        r"(?:projects?|personal projects?|key projects?)[:\s]*\n([\s\S]{0,1500}?)(?:\n[A-Z]{2,}|\Z)",
        text, re.IGNORECASE
    )
    if project_section:
        section_text = project_section.group(1)
        # Extract bullet points or numbered items
        bullets = re.findall(r"[•\-\*\d\.]\s+(.{20,200})", section_text)
        projects.extend(bullets[:5])

    # Pattern: "Built/Developed/Created/Implemented ..." sentences
    action_matches = re.findall(
        r"(?:built|developed|created|implemented|designed|architected|deployed|led)\s+(?:a\s+|an\s+)?(.{20,150}?)(?:[.\n]|$)",
        text, re.IGNORECASE
    )
    projects.extend(action_matches[:3])

    # Deduplicate
    seen = set()
    unique = []
    for p in projects:
        clean = p.strip()
        if clean and clean.lower() not in seen and len(clean) > 15:
            seen.add(clean.lower())
            unique.append(clean)

    return unique[:6]


def extract_experience_years(text: str) -> int:
    """Estimate years of experience from resume text."""
    # Look for "X years of experience" patterns
    patterns = [
        r"(\d+)\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"(\d+)\+?\s*years?\s+(?:working|in\s+the\s+industry)",
        r"experience\s*[:\-]?\s*(\d+)\+?\s*years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Estimate from year ranges (e.g., 2019-2024 = 5 years)
    year_ranges = re.findall(r"(20\d{2})\s*[-–]\s*(20\d{2}|present|current)", text, re.IGNORECASE)
    if year_ranges:
        total = 0
        for start, end in year_ranges:
            end_year = 2025 if end.lower() in ("present", "current") else int(end)
            total += max(0, end_year - int(start))
        return min(total, 20)  # Cap at 20

    return 0


# ── Main Parse Function ────────────────────────────────────────────────────────

def parse_resume(resume_text: str, use_llm: bool = True) -> dict:
    """
    Parse resume text and return structured data.
    Uses LLM if available, falls back to regex.

    Returns:
        {
            "skills": [...],
            "projects": [...],
            "experience_years": int,
            "key_technologies": [...],
            "summary": str
        }
    """
    if not resume_text or not resume_text.strip():
        return {
            "skills": [],
            "projects": [],
            "experience_years": 0,
            "key_technologies": [],
            "summary": "No resume provided.",
        }

    # Try LLM extraction first
    if use_llm:
        prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text[:3000])
        raw = call_llm(prompt, max_tokens=600)
        parsed = safe_parse_json(raw, fallback={})

        if parsed and "skills" in parsed:
            # Merge LLM output with regex fallback
            skills = parsed.get("skills", []) or extract_skills_regex(resume_text)
            projects = parsed.get("projects", []) or extract_projects_regex(resume_text)
            exp_years = parsed.get("experience_years", 0) or extract_experience_years(resume_text)
            key_tech = parsed.get("key_technologies", skills[:5])
        else:
            # LLM failed — use pure regex
            skills = extract_skills_regex(resume_text)
            projects = extract_projects_regex(resume_text)
            exp_years = extract_experience_years(resume_text)
            key_tech = skills[:5]
    else:
        skills = extract_skills_regex(resume_text)
        projects = extract_projects_regex(resume_text)
        exp_years = extract_experience_years(resume_text)
        key_tech = skills[:5]

    # Build human-readable summary
    summary_parts = []
    if exp_years > 0:
        summary_parts.append(f"{exp_years} years of experience")
    if key_tech:
        summary_parts.append(f"Key tech: {', '.join(key_tech[:5])}")
    if projects:
        summary_parts.append(f"Notable work: {projects[0][:80]}")
    summary = ". ".join(summary_parts) if summary_parts else "Resume parsed."

    return {
        "skills": skills,
        "projects": projects,
        "experience_years": exp_years,
        "key_technologies": key_tech,
        "summary": summary,
    }


def resume_context_for_prompt(parsed: dict) -> str:
    """Format parsed resume into a concise string for injection into prompts."""
    if not parsed or not parsed.get("skills"):
        return "No resume provided."

    parts = []
    if parsed.get("skills"):
        parts.append(f"Skills: {', '.join(parsed['skills'][:10])}")
    if parsed.get("experience_years"):
        parts.append(f"Experience: {parsed['experience_years']} years")
    if parsed.get("projects"):
        projects_str = " | ".join(p[:60] for p in parsed["projects"][:3])
        parts.append(f"Projects: {projects_str}")
    return "\n".join(parts)
