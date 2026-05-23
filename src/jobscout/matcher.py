"""AI-powered job matching engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jobscout.profile import UserProfile
from jobscout.providers.base import AIProvider, AIResponse
from jobscout.scraper import JobListing


@dataclass
class MatchResult:
    """Result of matching a profile to a job."""

    job: JobListing
    score: float
    reasoning: str
    skill_match: dict[str, float]
    missing_skills: list[str]
    strengths: list[str]
    improvement_tips: list[str]


MATCH_PROMPT = """You are an expert career counselor and job matching AI.

Given a candidate profile and a job listing, analyze the match and provide:
1. A match score (0-100)
2. Key matching strengths
3. Missing or weak skills
4. Tips to improve match

## Candidate Profile:
{profile}

## Job Listing:
{job}

Provide your analysis in this JSON format:
{{
    "score": <0-100>,
    "reasoning": "<brief explanation>",
    "skill_match": {{"<skill>": <0-1>}},
    "missing_skills": ["<skill1>", "<skill2>"],
    "strengths": ["<strength1>", "<strength2>"],
    "improvement_tips": ["<tip1>", "<tip2>"]
}}
"""


def _keyword_fallback_score(profile_text: str, job: JobListing) -> float:
    """Compute a basic keyword-overlap score when AI matching is unavailable."""
    if not profile_text or not job:
        return 50.0

    import re

    def _tokenize(text: str) -> set[str]:
        return {w.lower() for w in re.findall(r"\b[a-z][a-z0-9]+\b", text.lower()) if len(w) > 3}

    profile_words = _tokenize(profile_text)
    job_text = f"{job.title} {job.description} {' '.join(job.requirements)}"
    job_words = _tokenize(job_text)

    if not job_words:
        return 50.0

    overlap = len(profile_words & job_words)
    raw = min(overlap / max(len(job_words) * 0.3, 1), 1.0)
    score = 30.0 + raw * 50.0
    return round(score, 1)


class JobMatcher:
    """AI-powered job matching engine."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def match_profile_to_jobs(
        self,
        profile: UserProfile,
        jobs: list[JobListing],
        detailed: bool = False,
    ) -> list[MatchResult]:
        """Match a profile against multiple jobs."""
        results = []

        profile_text = profile.to_prompt_text()

        for job in jobs:
            result = self._match_single(profile_text, job, detailed)
            results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _match_single(
        self,
        profile_text: str,
        job: JobListing,
        detailed: bool = False,
    ) -> MatchResult:
        """Match a profile to a single job."""
        prompt = MATCH_PROMPT.format(
            profile=profile_text,
            job=job.to_prompt_text(),
        )

        system = "You are an expert career counselor. Return valid JSON only."

        try:
            response = self.provider.complete(
                prompt=prompt,
                system=system,
                max_tokens=1024,
            )
            return self._parse_match_response(response, job)
        except Exception as e:
            err_str = str(e)
            if err_str.strip().startswith("<") or "<!DOCTYPE" in err_str or "<html" in err_str:
                reasoning = "AI analysis unavailable — provider returned an unexpected response. Check your API key or provider settings."
            elif len(err_str) > 200:
                reasoning = "AI analysis unavailable — provider error (details truncated for display)"
            else:
                reasoning = f"AI analysis unavailable: {err_str}"

            fallback_score = _keyword_fallback_score(profile_text, job)

            return MatchResult(
                job=job,
                score=fallback_score,
                reasoning=reasoning,
                skill_match={},
                missing_skills=[],
                strengths=[f"Role at {job.company} in {job.location} — manual review recommended"],
                improvement_tips=["AI analysis is temporarily unavailable. Review the job description directly."],
            )

    def _parse_match_response(
        self,
        response: AIResponse,
        job: JobListing,
    ) -> MatchResult:
        """Parse AI response into MatchResult."""
        import json

        try:
            # Try to parse JSON from response
            content = response.content

            # Find JSON in response (in case there's extra text)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                content = content[start:end]

            data = json.loads(content)

            return MatchResult(
                job=job,
                score=data.get("score", 50.0),
                reasoning=data.get("reasoning", ""),
                skill_match=data.get("skill_match", {}),
                missing_skills=data.get("missing_skills", []),
                strengths=data.get("strengths", []),
                improvement_tips=data.get("improvement_tips", []),
            )
        except (json.JSONDecodeError, KeyError) as e:
            return MatchResult(
                job=job,
                score=50.0,
                reasoning=f"Failed to parse response: {e}",
                skill_match={},
                missing_skills=[],
                strengths=[],
                improvement_tips=[],
            )


class SkillGapAnalyzer:
    """Analyze skill gaps between profile and target roles."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def analyze_gaps(
        self,
        profile: UserProfile,
        target_roles: list[str],
    ) -> dict[str, Any]:
        """Analyze skill gaps for target roles."""
        prompt = f"""Analyze skill gaps for this candidate targeting these roles:
Roles: {', '.join(target_roles)}

Candidate Profile:
{profile.to_prompt_text()}

Provide:
1. Skills to emphasize
2. Skills to develop
3. Keywords to add to resume
4. Certifications that would help

Format as JSON with keys: emphasize_skills, develop_skills, keywords, certifications
"""

        try:
            response = self.provider.complete(prompt, max_tokens=1024)
            import json

            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                return json.loads(content[start:end])
        except Exception:
            return {
                "emphasize_skills": [],
                "develop_skills": [],
                "keywords": [],
                "certifications": [],
            }
