"""Heuristic job quality scoring and scam detection."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

SCAM_KEYWORDS = [
    "unlimited earning", "unlimited income", "be your own boss",
    "work from home earn", "no experience needed make money",
    "multi-level", "mlm", "pyramid", "commission only",
    "recruitment fee", "pay to join", "pay to work",
    "wire transfer", "western union", "money transfer agent",
    "you will earn $500/day", "guaranteed income",
    "no interview required", "immediate hire all applicants",
    "work 2 hours a day", "passive income opportunity",
]

WEAK_COMPANY_PATTERNS = [
    r"^(company|employer|confidential|anonymous|undisclosed)$",
    r"^[a-z]{1,3}$",   # too short
]


@dataclass
class QualityResult:
    score: int          # 0–100
    flags: list[str]


def score_job(
    title: str,
    company: str,
    description: str,
    url: str,
    posted_date: str = "",
    seen_keys: set[str] | None = None,
) -> QualityResult:
    """Score a job listing for quality/scam likelihood. Higher = better."""
    score = 100
    flags: list[str] = []

    # ── Duplicate detection ──────────────────────────────────────────
    if seen_keys is not None:
        key = _normalise_key(title, company)
        if key in seen_keys:
            score -= 40
            flags.append("duplicate_listing")
        else:
            seen_keys.add(key)

    # ── Company name ─────────────────────────────────────────────────
    if not company or company.strip().lower() in {"", "n/a", "unknown"}:
        score -= 25
        flags.append("missing_company")
    else:
        c = company.strip().lower()
        for pat in WEAK_COMPANY_PATTERNS:
            if re.match(pat, c, re.IGNORECASE):
                score -= 15
                flags.append("suspicious_company_name")
                break

    # ── Scam keyword scan ────────────────────────────────────────────
    text = (title + " " + description).lower()
    hits = [kw for kw in SCAM_KEYWORDS if kw in text]
    if hits:
        score -= min(50, len(hits) * 15)
        flags.append(f"scam_keywords:{','.join(hits[:3])}")

    # ── Stale listing ────────────────────────────────────────────────
    if posted_date:
        try:
            # Normalise: accept ISO string or unix epoch int/float
            if isinstance(posted_date, (int, float)):
                pd = datetime.fromtimestamp(posted_date, tz=UTC)
            else:
                pd = datetime.fromisoformat(str(posted_date).replace("Z", "+00:00"))
            age_days = (datetime.now(UTC) - pd).days
            if age_days > 180:
                score -= 20
                flags.append(f"stale_{age_days}d")
            elif age_days > 90:
                score -= 10
                flags.append(f"old_{age_days}d")
        except (ValueError, TypeError):
            pass

    # ── No real URL ──────────────────────────────────────────────────
    if not url or "example.com" in url or url.strip() in {"", "#"}:
        score -= 30
        flags.append("no_apply_link")

    # ── Short/empty description ──────────────────────────────────────
    if not description or len(description.strip()) < 50:
        score -= 20
        flags.append("missing_description")

    return QualityResult(score=max(0, min(100, score)), flags=flags)


def _normalise_key(title: str, company: str) -> str:
    """Create a normalised dedup key from title + company."""
    def clean(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower().strip())
    return f"{clean(title[:40])}|{clean(company[:30])}"
