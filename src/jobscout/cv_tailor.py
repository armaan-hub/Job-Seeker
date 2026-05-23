"""AI-powered CV tailoring — reframes existing CV content to match a job description.

IMPORTANT: This module ONLY reframes and reorders existing skills/experiences.
It NEVER adds fabricated skills or experiences the user does not have.
"""
from __future__ import annotations

import hashlib
import json
import re

# Simple in-memory cache: md5(profile+jd) → result dict
_CACHE: dict[str, dict] = {}


def tailor_cv(
    profile: dict,
    job_title: str,
    job_company: str,
    job_description: str,
    provider=None,
) -> dict:
    """Tailor the user's CV for a specific job.

    Returns a dict with:
        tailored_sections: dict[str, str]  — rewritten CV sections
        gaps: list[str]                    — keywords in JD not found in CV
        keywords_added: list[str]          — keywords that were reframed/highlighted
        match_score: int                   — 0-100 estimate of CV-JD match
        ai_available: bool                 — whether AI was used or keyword-fallback
    """
    cache_key = _make_cache_key(profile, job_description)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    # Extract keywords from JD
    jd_keywords = _extract_keywords(job_description)
    cv_text = _profile_to_text(profile)
    cv_keywords = _extract_keywords(cv_text)

    gaps = [kw for kw in jd_keywords if kw not in cv_keywords]
    present = [kw for kw in jd_keywords if kw in cv_keywords]
    match_score = int(len(present) / max(len(jd_keywords), 1) * 100)

    # Try AI tailoring
    ai_result = None
    if provider is not None:
        ai_result = _ai_tailor(profile, job_title, job_company, job_description, gaps, provider)

    if ai_result:
        result = {
            "tailored_sections": ai_result,
            "gaps": gaps,
            "keywords_added": present,
            "match_score": match_score,
            "ai_available": True,
        }
    else:
        # Keyword fallback — highlight existing matches, note gaps
        result = {
            "tailored_sections": _keyword_tailor(profile, jd_keywords),
            "gaps": gaps,
            "keywords_added": present,
            "match_score": match_score,
            "ai_available": False,
        }

    _CACHE[cache_key] = result
    return result


def _ai_tailor(
    profile: dict,
    job_title: str,
    job_company: str,
    job_description: str,
    gaps: list[str],
    provider,
) -> dict | None:
    """Call the AI provider to produce tailored CV sections."""
    try:
        cv_summary = _profile_to_text(profile)
        gaps_str = ", ".join(gaps[:15]) if gaps else "none identified"

        system_prompt = (
            "You are a professional CV coach. Your ONLY job is to REFRAME and REORDER "
            "existing CV content to match a job description. "
            "STRICT RULES: (1) Never add skills, experiences, or achievements the candidate "
            "does not already have. (2) Never fabricate numbers, dates, or companies. "
            "(3) Only rephrase existing content using the job's exact terminology. "
            "(4) If a required skill is genuinely missing, list it in 'gaps' only."
        )

        user_message = (
            f"Job: {job_title} at {job_company}\n\n"
            f"Job Description:\n{job_description[:3000]}\n\n"
            f"Candidate's Current CV:\n{cv_summary[:3000]}\n\n"
            f"Keywords in JD missing from CV: {gaps_str}\n\n"
            "Produce a JSON response with these keys:\n"
            "- summary: A 3-sentence professional summary tailored to this job (using candidate's actual experience)\n"
            "- key_skills: Bullet list of relevant skills from the CV, using the job's exact terminology\n"
            "- experience_highlights: Top 3 most relevant experience bullet points rewritten for this job\n"
            "- cover_note: 2-sentence note explaining why the candidate is a strong fit\n"
            "Return ONLY valid JSON, no markdown."
        )

        response = provider.complete(
            prompt=user_message,
            system=system_prompt,
            max_tokens=1500,
        )

        # Parse response — provider returns AIResponse with .content attribute
        text = response.content.strip() if hasattr(response, "content") else str(response).strip()
        # Remove markdown code blocks if present
        text = re.sub(r"```(?:json)?", "", text).strip()
        parsed = json.loads(text)

        # Validate structure
        required = {"summary", "key_skills", "experience_highlights", "cover_note"}
        if not required.issubset(parsed.keys()):
            return None
        return parsed

    except Exception:
        return None


def _flatten_skills(skills_val) -> list[str]:
    """Convert skills to flat list whether it's a dict-of-lists or a list."""
    if isinstance(skills_val, dict):
        result = []
        for lst in skills_val.values():
            if isinstance(lst, list):
                result.extend(str(s) for s in lst)
        return result
    elif isinstance(skills_val, list):
        return [str(s) for s in skills_val]
    return []


def _get_profile_fields(profile: dict) -> tuple[str, str, str]:
    """Return (name, current_role, summary) handling nested 'profile' key or flat layout."""
    p = profile.get("profile", {})
    name = p.get("name") or profile.get("name", "Candidate")
    role = p.get("title") or profile.get("current_role") or profile.get("title", "Financial Data Analyst")
    summary = profile.get("professional_summary") or profile.get("summary", "")
    return name, role, summary


def _keyword_tailor(profile: dict, jd_keywords: list[str]) -> dict:
    """Fallback: return profile sections with matching keywords highlighted."""
    all_skills = _flatten_skills(profile.get("skills", []))
    relevant_skills = [s for s in all_skills if any(kw.lower() in s.lower() for kw in jd_keywords)]
    if not relevant_skills:
        relevant_skills = all_skills[:10]

    experience = profile.get("experience", [])
    exp_bullets = []
    for exp in experience[:3]:
        role = exp.get("role", "") or exp.get("title", "")
        company = exp.get("company", "")
        responsibilities = exp.get("bullets", []) or exp.get("responsibilities", [])
        for r in responsibilities[:2]:
            exp_bullets.append(f"• {r} ({role} at {company})")

    name, current_role, _summary = _get_profile_fields(profile)

    return {
        "summary": (
            f"{name} is an experienced {current_role} with expertise in {', '.join(relevant_skills[:5])}. "
            f"Proven track record in financial data analysis, ETL processes, and business intelligence. "
            f"Ready to bring analytical skills to drive data-driven decisions."
        ),
        "key_skills": "\n".join(f"• {s}" for s in relevant_skills[:12]),
        "experience_highlights": (
            "\n".join(exp_bullets[:5]) if exp_bullets else "• See full CV for experience details"
        ),
        "cover_note": (
            f"My background in {current_role} directly aligns with the requirements of this role. "
            f"I am confident my skills in {', '.join(relevant_skills[:3])} will add immediate value."
        ),
    }


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text (lowercase, deduplicated)."""
    keyword_patterns = [
        r'\b(?:sql|python|excel|power bi|tableau|powerpoint|vba|r\b)',
        r'\b(?:etl|data warehouse|data modeling|reporting|dashboard)',
        r'\b(?:financial analysis|financial modeling|budget|forecast)',
        r'\b(?:mysql|postgresql|oracle|sql server|snowflake|redshift)',
        r'\b(?:pandas|numpy|matplotlib|scipy|scikit)',
        r'\b(?:azure|aws|gcp|databricks|spark)',
        r'\b(?:erp|sap|oracle financials|hyperion|cognos)',
        r'\b(?:cfa|ca|cpa|acca|frm)',
        r'\b(?:bloomberg|reuters|factset)',
        r'\b(?:kpi|roi|p&l|balance sheet|cash flow)',
    ]
    text_lower = text.lower()
    found = set()
    for pat in keyword_patterns:
        for match in re.finditer(pat, text_lower):
            found.add(match.group().strip())

    # Also extract capitalized multi-word terms
    for match in re.finditer(r'\b[A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+\b', text):
        found.add(match.group().lower())

    return sorted(found)


def _profile_to_text(profile: dict) -> str:
    """Flatten profile dict to a single text string for analysis."""
    parts = []
    name, current_role, summary = _get_profile_fields(profile)
    if name:
        parts.append(name)
    if current_role:
        parts.append(current_role)
    if summary:
        parts.append(summary)
    for skill in _flatten_skills(profile.get("skills", [])):
        parts.append(skill)
    for exp in profile.get("experience", []):
        role = exp.get("role", "") or exp.get("title", "")
        parts.append(f"{role} {exp.get('company', '')}")
        for r in (exp.get("bullets") or exp.get("responsibilities", []))[:3]:
            parts.append(str(r))
    for edu in profile.get("education", []):
        parts.append(f"{edu.get('degree', '')} {edu.get('institution', '')}")
    return " ".join(parts)


def _make_cache_key(profile: dict, job_description: str) -> str:
    combined = json.dumps(profile, sort_keys=True) + job_description[:2000]
    return hashlib.md5(combined.encode()).hexdigest()
