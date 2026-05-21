# Design Spec: Job Advisor Features

**Date:** 2026-05-21
**Project:** AI Job Scout (`job-scout/`)
**Author:** Aniket Kumar Mishra + Copilot
**Status:** Approved

---

## Overview

Add three new AI-powered advisor features to help job seekers not just find jobs, but win them:

1. **Resume Advisor** — Targeted CV edit suggestions tailored to a specific job
2. **Requirements Analyzer** — Side-by-side comparison of job requirements vs candidate profile, with priority ranking
3. **Application Coach** — Quick tips + full action plan for getting the job

These features are accessible via a new `advise` CLI command, with a quick summary inline during `search`.

---

## User Stories

1. As a job seeker, I want to see exactly which lines of my CV to rewrite for a specific job so I can quickly tailor my application.
2. As a job seeker, I want to see a clear comparison of what a job requires vs what I have, so I know my gaps.
3. As a job seeker, I want actionable advice on how to best approach and land a specific job.

---

## Architecture

### New File: `src/jobscout/advisor.py`

Three classes, each with a single responsibility and a shared `AIProvider`:

```
advisor.py
├── ResumeAdvisor.suggest_edits(profile, job) → list[ResumeEdit]
├── RequirementsAnalyzer.analyze(profile, job) → RequirementsReport
└── ApplicationCoach.advise(profile, job, include_plan) → CoachAdvice
```

**Data classes:**

```python
@dataclass
class ResumeEdit:
    section: str          # e.g. "Experience at ENBD"
    current_text: str     # what's currently in the CV
    suggested_text: str   # what to change it to
    reason: str           # why this edit helps for this job

@dataclass
class Requirement:
    item: str             # e.g. "Power BI experience"
    priority: str         # "must-have" or "nice-to-have"
    candidate_has: bool   # True if profile covers it
    candidate_note: str   # e.g. "5 years Power BI" or "Not mentioned"

@dataclass
class RequirementsReport:
    requirements: list[Requirement]
    coverage_score: float          # 0-100
    critical_gaps: list[str]       # must-haves the candidate lacks

@dataclass
class CoachAdvice:
    quick_tips: list[str]                        # 3-5 high-impact actions
    action_plan: dict[str, list[str]] | None     # keys: before_applying, cover_letter, interview_prep
                                                 # None if --plan not requested
```

### Modified: `src/jobscout/main.py`

**`search` command changes:**
- After AI matching, save all `MatchResult` objects to `~/.jobscout/last_results.json` (serialized)
- Number each result `[1]`, `[2]` in display output
- With `--detailed` flag: show 1-line quick tip per result inline

**New `advise` command:**
```
job-scout advise <index>            # Full advice for job #N from last search
job-scout advise <index> --plan     # + full step-by-step action plan
job-scout advise --desc-file f.txt  # Fallback: job description from a file
```

### State File: `~/.jobscout/last_results.json`

Written by `search`, read by `advise`. Format:

```json
{
  "timestamp": "2026-05-21T18:00:00",
  "jobs": [
    {
      "index": 1,
      "title": "...",
      "company": "...",
      "location": "...",
      "source": "...",
      "description": "...",
      "url": "...",
      "score": 85.0
    }
  ]
}
```

---

## CLI Interface

### `search` (updated output format)

```
[1] Senior Data Analyst at Emirates NBD               Score: 87%
    💡 Tip: Highlight your 5-year Power BI and AML compliance experience
[2] Power BI Developer at ADIB                        Score: 74%
    💡 Tip: Add SQL Server and Azure certifications to stand out
...

✅ Results saved. Run `job-scout advise <number>` for full advice on any job.
```

### `advise <index>` (new command output)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Senior Data Analyst at Emirates NBD | Dubai, UAE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 JOB REQUIREMENTS ANALYSIS  (Coverage: 83%)

  Requirement                   Priority     You Have?
  ─────────────────────────────────────────────────────
  Power BI dashboards           Must-have    ✅ 5 years
  SQL / Data warehousing        Must-have    ✅ Strong
  AML/KYC compliance reporting  Must-have    ✅ 3 years
  Azure Data Factory            Must-have    ❌ Not in CV
  Python for automation         Nice-to-have ✅ Certified
  Tableau                       Nice-to-have ❌ Not in CV

  🔴 Critical gaps: Azure Data Factory

✍️  RESUME EDITS (3 targeted changes)

  1. Experience → Nextracker (Current Role)
     CURRENT: "Managed financial reporting and ETL pipelines"
     SUGGEST: "Designed and automated ETL pipelines using Python and Power
               Query, processing 6M+ records monthly for financial reporting"
     WHY: Job requires ETL + volume evidence; makes the match explicit

  2. Skills Section
     CURRENT: "Power BI, VBA, Python, SQL"
     SUGGEST: "Power BI (5 yrs), SQL Server, Python (automation), AML/KYC
               compliance reporting, Power Query, ETL pipeline design"
     WHY: ATS keyword match; job lists these exact terms

  3. Summary / Headline
     CURRENT: "Financial Data Analyst | Automation Specialist"
     SUGGEST: "Senior Financial Data Analyst | Power BI | ETL | AML/KYC |
               Certified AI Professional"
     WHY: Mirrors the job title and top keywords in the first 6 seconds

🎯 QUICK TIPS (5 high-impact actions)

  1. Add "Azure Data Factory" to your learning plan and mention it in your
     cover letter as an in-progress skill
  2. Tailor your cover letter opening to reference ENBD's recent digital
     transformation initiatives
  3. Quantify impact in your resume: "reduced reporting time by X%"
  4. Get a LinkedIn recommendation from a manager covering your AML work
  5. Apply via a referral if possible — ENBD frequently posts internal jobs

Run with --plan for a full step-by-step action plan.
```

### `advise <index> --plan` (additional section)

```
📅 FULL ACTION PLAN

  BEFORE APPLYING
  ───────────────
  ☐ 1. Update CV with the 3 targeted edits above (est. 30 mins)
  ☐ 2. Write a tailored cover letter referencing ENBD digital transformation
  ☐ 3. Check LinkedIn for mutual connections at Emirates NBD
  ☐ 4. Research ENBD's latest financial reports and data initiatives

  COVER LETTER ANGLE
  ──────────────────
  Open with your AML/KYC compliance background (directly relevant),
  bridge to your Power BI impact (6M+ records), close by expressing
  fit for ENBD's digital transformation. Keep under 250 words.

  INTERVIEW PREPARATION
  ─────────────────────
  ☐ Prepare 2 STAR stories: (1) complex ETL project, (2) compliance reporting
  ☐ Know ENBD's tech stack: likely Microsoft-centric (Power BI, Azure)
  ☐ Prepare questions about team size, data maturity, and projects
  ☐ Review UAE banking regulations relevant to AML reporting
```

---

## AI Prompts

### ResumeAdvisor prompt
```
You are an expert CV coach. Given a candidate profile and a specific job listing,
suggest exactly 3-5 targeted edits the candidate should make to their CV to
maximize their match for this job. Focus on rewriting existing content, not
adding new lies. Be specific: which section, what to change, and why.

Return JSON: [{"section": "...", "current_text": "...", "suggested_text": "...", "reason": "..."}]
```

### RequirementsAnalyzer prompt
```
You are a hiring expert. Extract ALL requirements from this job listing and
determine whether this candidate meets each one. Label each as "must-have"
or "nice-to-have". For each, indicate if the candidate has it and any relevant
evidence from their profile.

Return JSON: {"requirements": [...], "coverage_score": 0-100, "critical_gaps": [...]}
```

### ApplicationCoach prompt
```
You are a career coach. Given this candidate's profile and a specific job, give:
1. 3-5 high-impact quick tips to maximize chances of getting this job
2. A detailed action plan covering: before-applying, cover-letter angle, interview-prep

Return JSON: {"quick_tips": [...], "action_plan": {"before_applying": [...], "cover_letter": "...", "interview_prep": [...]}}
```

---

## Error Handling

- If `last_results.json` doesn't exist: print helpful message → "Run `job-scout search` first"
- If index is out of range: print clear error with valid range
- If AI fails on any advisor: show fallback message, do not crash
- If `--desc-file` file not found: standard click error

---

## Testing

- Unit test `ResumeAdvisor`, `RequirementsAnalyzer`, `ApplicationCoach` with mock provider
- Test JSON parsing / fallback on malformed AI responses
- Test `last_results.json` save/load round-trip
- Test `advise` CLI command with mocked state file
- All tests in `tests/test_advisor.py`

---

## Out of Scope (not in this spec)

- Email/cover letter generation (future feature)
- Saving multiple search sessions (only last results saved)
- PDF output of advice (future feature)
- URL-based job input (blocked on real scrapers)
