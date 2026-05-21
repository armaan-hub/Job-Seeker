# AI Job Scout

An intelligent CLI tool that matches your CV/resume against job listings using AI-powered matching.

## Features

- **AI-Powered Matching**: Uses Claude/OpenAI/OpenCode to match your profile with relevant jobs
- **Multi-Source Job Scraping**: Fetches from LinkedIn, Indeed, Bayt, Naukri Gulf
- **Skill Gap Analysis**: Identifies areas for improvement
- **Resume Optimization**: Get tips for tailoring your resume per job
- **Multiple AI Providers**: Configurable (Anthropic, OpenAI, OpenCode)
- **Rich CLI Output**: Beautiful terminal interface with tables and panels

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/armaan-hub/Job-Seeker.git
cd Job-Seeker
pip install -e ".[dev]"
```

### 2. Configure

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Anthropic Claude (Recommended)
ANTHROPIC_API_KEY=sk-ant-...

# Or OpenAI GPT
OPENAI_API_KEY=sk-...

# Active provider
ACTIVE_PROVIDER=anthropic
```

### 3. Run

```bash
# Search for jobs matching your profile
jobscout search --profile data/profile.json --location "Dubai, UAE" --roles "Data Analyst"

# Run skill gap analysis
jobscout analyze --profile data/profile.json

# See provider status
jobscout providers
```

## Usage

### Search Command

```bash
jobscout search [OPTIONS]

Options:
  --profile PATH          Path to profile JSON file
  --location TEXT        Job location filter (default: Dubai, UAE)
  --roles TEXT           Job roles to search for (can specify multiple)
  --sources TEXT         Job sources to use (linkedin, indeed, bayt, naukrigulf, mock)
  --max-results INTEGER   Maximum number of jobs to return (default: 10)
  --detailed             Show detailed match analysis
  --analyze-skills       Run skill gap analysis
```

### Analyze Command

```bash
jobscout analyze --profile data/profile.json
```

### Providers Command

```bash
jobscout providers
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/

# Format
black src/

# Type check
mypy src/
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ User Input   │────▶│   Profile   │────▶│    AI       │
│ (CV/JSON)   │     │   Parser    │     │   Matcher   │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Results   │◀────│    Ranker    │◀────│ Job Listings│
│  (Matches)  │     │              │     │  (Scraped)  │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Project Structure

```
job-scout/
├── src/jobscout/
│   ├── main.py           # CLI entry point
│   ├── config.py         # Configuration management
│   ├── profile.py        # CV/resume parsing
│   ├── matcher.py       # AI job matching engine
│   ├── scraper.py        # Job board integrations
│   └── providers/        # AI provider adapters
│       ├── base.py       # Abstract base class
│       ├── anthropic.py  # Claude provider
│       ├── openai.py     # GPT provider
│       └── opencode.py   # OpenCode proxy provider
├── tests/                # Test suite
├── data/                # Profile data
├── pyproject.toml       # Project configuration
└── .env.example         # Environment template
```

## Supported Job Sources

- LinkedIn
- Indeed
- Bayt
- Naukri Gulf
- Mock (for development/testing)

## Supported AI Providers

| Provider | Model | Status |
|----------|-------|--------|
| Anthropic Claude | Sonnet 4.7 | Recommended |
| OpenAI GPT | GPT-4o | Available |
| OpenCode Proxy | Multiple | Available |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -m "feat: add my feature"`
3. Push: `git push origin feature/my-feature`
4. Open a Pull Request

---

Built with Claude Code by Aniket Kumar Mishra
