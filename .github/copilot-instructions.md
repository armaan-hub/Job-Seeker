# AI Job Scout — Copilot Instructions

## Project

AI-powered CLI job finder for Aniket Kumar Mishra (Financial Data Analyst, Dubai UAE).  
User profile: `data/profile.json` | Introduction: `../My Instroduction/aniket_profile.json`  
GitHub: https://github.com/armaan-hub/Job-Seeker

## Commands

```bash
pip install -e ".[dev]"            # Install with dev deps

python3 -m pytest tests/ -v        # Run all tests
python3 -m pytest tests/test_profile.py::TestProfileParser::test_load_json_profile  # Single test

ruff check src/                    # Lint
ruff check src/ --fix              # Auto-fix lint
black src/                         # Format

jobscout search --sources mock --detailed                  # Run with mock data (no API key needed)
jobscout search --profile data/profile.json --sources mock # Explicit profile
jobscout analyze --profile data/profile.json               # Skill gap analysis
jobscout providers                                         # Show provider status
```

## Architecture

```
User Profile (JSON/MD)
       │
   profile.py  ──── parse ──▶  UserProfile dataclass
                                      │
scraper.py ──── JobListing[]──▶  matcher.py ──▶ MatchResult[] (sorted by score)
  (per source)                        │
                               providers/
                           anthropic | openai | opencode
```

**Key data flows:**
- `ProfileParser.load_profile(path)` → reads JSON → `UserProfile.from_dict()`
- `JobMatcher.match_profile_to_jobs(profile, jobs)` → calls AI → parses JSON response → `MatchResult`
- `SkillGapAnalyzer.analyze_gaps(profile, roles)` → calls AI → returns dict with emphasize/develop/keywords/certifications

## Key Conventions

### Profile JSON structure
```json
{
  "profile": { "name": "...", "title": "...", "contact": { ... } },
  "professional_summary": "...",
  "experience": [ { "company": "...", "role": "...", "start": "YYYY-MM", ... } ],
  "skills": { "data_engineering": [...], "finance": [...] },
  "target_roles": [...],
  "key_metrics": { "years_experience": 10, ... }
}
```
Note: `title` is nested under `profile.{}`, not at root.

### AI Provider pattern
All providers implement `AIProvider.complete(prompt, system, **kwargs) → AIResponse`.
- **Anthropic**: `system` is a top-level kwarg to `messages.create()`, NOT a role in messages array
- **OpenAI/OpenCode**: `system` is a `{"role": "system", ...}` message prepended to messages array
- AI responses always return raw JSON — use `json.loads()` on the `.content` field

### Scraper pattern
All scrapers inherit `JobScraper` and implement `search(roles, location, max_results) → list[JobListing]`.
- LinkedIn, Indeed, Bayt, NaukriGulf are **stubs** (return `[]`) — real scraping not yet implemented
- Use `mock` source for development/testing: `--sources mock`

### Configuration
- All secrets via `.env` (copy `.env.example`)
- `ACTIVE_PROVIDER=anthropic|openai|opencode`
- Default provider: `anthropic` — requires `ANTHROPIC_API_KEY`
- OpenCode uses local proxy at `http://localhost:4001` (from Claude-Opencode-Ollama repo)

### Code standards
- Python 3.11+ type hints required on all functions
- `ruff` line length: 100 chars
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- No API keys in code — always `.env`

## What's Not Yet Implemented

- Real scrapers for LinkedIn, Indeed, Bayt, NaukriGulf (all return empty lists)
- PDF/DOCX CV parsing (returns empty `UserProfile`)
- Markdown profile parsing (returns empty `UserProfile`)

When implementing scrapers, add them to `scraper.py` by extending the stub classes. Test with the mock scraper pattern.
