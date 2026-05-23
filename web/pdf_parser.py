"""PDF CV parser — extracts text then uses AI to build a profile dict."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    try:
        import pdfplumber  # type: ignore[import]

        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        return _fallback_pypdf(pdf_path)


def _fallback_pypdf(pdf_path: Path) -> str:
    """Fallback PDF text extraction via PyPDF2."""
    try:
        from PyPDF2 import PdfReader  # type: ignore[import]

        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as exc:
        raise RuntimeError(f"Could not extract text from PDF: {exc}") from exc


_EXTRACTION_PROMPT = """You are an expert CV/resume parser. Extract the information from the CV text below and return ONLY a valid JSON object matching this exact schema (no markdown, no explanation, just JSON):

{{
  "profile": {{
    "name": "Full Name",
    "title": "Job Title",
    "contact": {{
      "email": "",
      "phone": "",
      "location": "",
      "linkedin": ""
    }}
  }},
  "professional_summary": "...",
  "experience": [
    {{
      "company": "",
      "location": "",
      "role": "",
      "start": "YYYY-MM",
      "end": "Present or YYYY-MM",
      "key_achievement": "",
      "bullets": ["...", "..."]
    }}
  ],
  "education": [
    {{
      "institution": "",
      "degree": "",
      "field": "",
      "year": ""
    }}
  ],
  "skills": {{
    "technical": ["skill1", "skill2"],
    "tools": ["tool1", "tool2"],
    "domain": ["domain1", "domain2"],
    "soft": ["soft1", "soft2"]
  }},
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "year": ""
    }}
  ],
  "target_roles": ["Role1", "Role2"],
  "preferred_locations": ["Location1"]
}}

If a field is not found in the CV, use an empty string "" or empty array []. For target_roles, infer from the person's experience and title what roles they are best suited for.

CV TEXT:
{cv_text}

Return ONLY the JSON object, nothing else."""


def ai_parse_cv_text(cv_text: str, provider: Any) -> dict[str, Any]:
    """Send CV text to AI provider and parse the returned JSON profile."""
    prompt = _EXTRACTION_PROMPT.format(cv_text=cv_text[:8000])  # stay within token limits

    try:
        response = provider.complete(prompt, model=provider.default_model.name)
        raw = response.content.strip()
    except Exception as exc:
        raise RuntimeError(f"AI extraction failed: {exc}") from exc

    # Strip any markdown code fences the model might wrap around JSON
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON object boundaries
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        raise RuntimeError(f"AI returned non-JSON response: {raw[:200]}") from None


def minimal_profile_from_text(cv_text: str) -> dict[str, Any]:
    """Build a minimal profile dict from raw CV text (no-AI fallback)."""
    # Extract name heuristically — first line that looks like a name
    lines = [ln.strip() for ln in cv_text.split("\n") if ln.strip()]
    name = lines[0] if lines else "Candidate"

    # Try to find email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", cv_text)
    email = email_match.group(0) if email_match else ""

    # Try phone
    phone_match = re.search(r"[\+\d][\d\s\-\(\)]{8,15}", cv_text)
    phone = phone_match.group(0).strip() if phone_match else ""

    return {
        "profile": {
            "name": name,
            "title": "Professional",
            "contact": {
                "email": email,
                "phone": phone,
                "location": "",
            },
        },
        "professional_summary": cv_text[:500],
        "experience": [],
        "education": [],
        "skills": {"technical": [], "tools": [], "domain": [], "soft": []},
        "certifications": [],
        "target_roles": [],
        "preferred_locations": [],
    }
