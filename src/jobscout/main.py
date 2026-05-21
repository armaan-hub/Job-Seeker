"""CLI entry point for Job Scout."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from jobscout import __version__
from jobscout.advisor import ApplicationCoach, RequirementsAnalyzer, ResumeAdvisor
from jobscout.config import JobScoutConfig, get_config
from jobscout.matcher import JobMatcher, MatchResult, SkillGapAnalyzer
from jobscout.profile import ProfileParser
from jobscout.providers.anthropic import AnthropicProvider
from jobscout.providers.openai import OpenAIProvider
from jobscout.providers.opencode import OpenCodeProvider
from jobscout.scraper import get_scraper
from jobscout.state import load_job_at_index, save_results

console = Console()


def get_provider(config: JobScoutConfig):
    """Get the configured AI provider."""
    if config.active_provider == "anthropic":
        return AnthropicProvider(config.anthropic.api_key)
    elif config.active_provider == "openai":
        return OpenAIProvider(config.openai.api_key)
    elif config.active_provider == "opencode":
        return OpenCodeProvider(
            base_url=config.opencode.base_url,
            api_key=config.opencode.api_key,
        )
    else:
        raise ValueError(f"Unknown provider: {config.active_provider}")


def format_match_result(result: MatchResult, detailed: bool = False) -> None:
    """Format and print a single match result."""
    score = result.score
    score_color = (
        "green" if score >= 70 else "yellow" if score >= 50 else "red"
    )

    panel_content = [
        f"[bold]Score:[/bold] [{score_color}]{score:.0f}%[/]"
    ]

    if detailed:
        panel_content.extend([
            f"[bold]Reasoning:[/bold] {result.reasoning}",
            "",
            f"[bold]Strengths:[/bold] {', '.join(result.strengths) if result.strengths else 'N/A'}",
        ])
        if result.missing_skills:
            panel_content.append(f"[bold]Missing Skills:[/bold] {', '.join(result.missing_skills)}")
        if result.improvement_tips:
            panel_content.append(f"[bold]Tips:[/bold] {result.improvement_tips[0]}")

    console.print(Panel(
        "\n".join(panel_content),
        title=f"[bold]{result.job.title}[/bold] at {result.job.company}",
        subtitle=f"{result.job.location} | Source: {result.job.source}",
        border_style="blue",
    ))


def display_skill_analysis(analysis: dict) -> None:
    """Display skill gap analysis."""
    console.print("\n[bold cyan]Skill Gap Analysis[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category")
    table.add_column("Items")

    if analysis.get("emphasize_skills"):
        table.add_row("Emphasize", ", ".join(analysis["emphasize_skills"]))
    if analysis.get("develop_skills"):
        table.add_row("Develop", ", ".join(analysis["develop_skills"]))
    if analysis.get("keywords"):
        table.add_row("Keywords", ", ".join(analysis["keywords"]))
    if analysis.get("certifications"):
        table.add_row("Certifications", ", ".join(analysis["certifications"]))

    console.print(table)


def display_resume_edits(edits) -> None:
    """Display resume edit suggestions."""
    from jobscout.advisor import ResumeEdit  # noqa: F401
    console.print("\n[bold cyan]📄 Resume Edits[/bold cyan]")
    if not edits:
        console.print("[dim]No edits suggested.[/dim]")
        return
    for i, edit in enumerate(edits, 1):
        console.print(Panel(
            f"[bold]Current:[/bold] {edit.current_text}\n"
            f"[bold green]Suggested:[/bold green] {edit.suggested_text}\n"
            f"[bold]Why:[/bold] {edit.reason}",
            title=f"[{i}] {edit.section}",
            border_style="cyan",
        ))


def display_requirements_report(report) -> None:
    """Display requirements coverage report."""
    score = report.coverage_score
    score_color = "green" if score >= 70 else "yellow" if score >= 50 else "red"
    console.print(f"\n[bold cyan]📋 Requirements Analysis[/bold cyan]  "
                  f"Coverage: [{score_color}]{score:.0f}%[/]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Requirement")
    table.add_column("Priority")
    table.add_column("You Have It?")
    table.add_column("Notes")

    for req in report.requirements:
        has_it = "[green]✓[/green]" if req.candidate_has else "[red]✗[/red]"
        priority_color = "red" if req.priority == "must-have" else "yellow"
        table.add_row(
            req.item,
            f"[{priority_color}]{req.priority}[/]",
            has_it,
            req.candidate_note,
        )
    console.print(table)

    if report.critical_gaps:
        console.print(f"[red bold]Critical gaps:[/red bold] {', '.join(report.critical_gaps)}")


def display_coach_advice(advice) -> None:
    """Display application coaching advice."""
    console.print("\n[bold cyan]🎯 Application Coach[/bold cyan]")
    for tip in advice.quick_tips:
        console.print(f"  • {tip}")

    if advice.action_plan:
        console.print("\n[bold]Action Plan:[/bold]")
        labels = {
            "before_applying": "Before Applying",
            "cover_letter": "Cover Letter",
            "interview_prep": "Interview Prep",
        }
        for key, steps in advice.action_plan.items():
            label = labels.get(key, key.replace("_", " ").title())
            console.print(f"\n  [bold yellow]{label}:[/bold yellow]")
            for step in steps:
                console.print(f"    → {step}")


@click.group()
@click.version_option(version=__version__)
def main():
    """AI Job Scout — Find jobs that match your profile."""
    pass


@main.command()
@click.option(
    "--profile",
    type=click.Path(exists=True, path_type=Path),
    help="Path to profile JSON file",
)
@click.option(
    "--location",
    default="Dubai, UAE",
    help="Job location filter",
)
@click.option(
    "--roles",
    multiple=True,
    help="Job roles to search for (can specify multiple)",
)
@click.option(
    "--sources",
    multiple=True,
    help="Job sources to use (linkedin, indeed, bayt, naukrigulf, mock)",
)
@click.option(
    "--max-results",
    default=10,
    type=int,
    help="Maximum number of jobs to return",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Show detailed match analysis",
)
@click.option(
    "--analyze-skills",
    is_flag=True,
    help="Run skill gap analysis",
)
def search(
    profile: Path | None,
    location: str,
    roles: tuple[str, ...],
    sources: tuple[str, ...],
    max_results: int,
    detailed: bool,
    analyze_skills: bool,
):
    """Search for jobs matching your profile."""
    config = get_config()

    # Load profile
    if profile:
        try:
            user_profile = ProfileParser.load_profile(profile)
            console.print(f"[green]Loaded profile:[/green] {user_profile.name or profile.name}")
        except Exception as e:
            console.print(f"[red]Error loading profile:[/red] {e}")
            sys.exit(1)
    else:
        # Use default profile path if exists
        default_profile = Path("My Instroduction/aniket_profile.json")
        if default_profile.exists():
            user_profile = ProfileParser.load_profile(default_profile)
            console.print(f"[green]Using default profile:[/green] {user_profile.name}")
        else:
            console.print("[yellow]Warning:[/yellow] No profile loaded, using defaults")
            from jobscout.profile import UserProfile
            user_profile = UserProfile()

    # Determine roles
    target_roles = list(roles) if roles else config.default_roles

    # Determine sources
    job_sources = list(sources) if sources else config.job_sources

    console.print(f"\n[bold]Searching for:[/bold] {', '.join(target_roles)}")
    console.print(f"[bold]Location:[/bold] {location}")
    console.print(f"[bold]Sources:[/bold] {', '.join(job_sources)}\n")

    # Scrape jobs
    all_jobs = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for source in job_sources:
            task = progress.add_task(f"Scraping {source}...", total=None)
            scraper = get_scraper(source)
            jobs = scraper.search(roles=target_roles, location=location, max_results=max_results)
            all_jobs.extend(jobs)
            progress.update(task, completed=True)

    if not all_jobs:
        console.print("[yellow]No jobs found.[/yellow]")
        return

    console.print(f"[green]Found {len(all_jobs)} jobs[/green]\n")

    # Match jobs with AI
    try:
        provider = get_provider(config)
        matcher = JobMatcher(provider)

        with console.status("[bold green]Analyzing matches with AI..."):
            results = matcher.match_profile_to_jobs(user_profile, all_jobs, detailed)

        # Display top matches
        top_results = results[:max_results]
        console.print(f"\n[bold cyan]Top {len(top_results)} Matches:[/bold cyan]\n")

        for idx, result in enumerate(top_results, start=1):
            console.print(f"[dim]\\[{idx}][/dim]", end=" ")
            format_match_result(result, detailed)

        # Persist results for advise command
        save_results(
            [r.job for r in top_results],
            [r.score for r in top_results],
        )
        console.print(
            "\n[dim]💡 Tip: Run [bold]job-scout advise <N>[/bold] for AI coaching on any result above.[/dim]"
        )

        # Skill gap analysis
        if analyze_skills:
            analyzer = SkillGapAnalyzer(provider)
            analysis = analyzer.analyze_gaps(user_profile, target_roles)
            display_skill_analysis(analysis)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--profile",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to profile JSON file",
)
def analyze(profile: Path):
    """Analyze skill gaps for a profile."""
    config = get_config()

    try:
        user_profile = ProfileParser.load_profile(profile)
        provider = get_provider(config)
        analyzer = SkillGapAnalyzer(provider)

        with console.status("[bold green]Analyzing skill gaps..."):
            analysis = analyzer.analyze_gaps(user_profile, user_profile.target_roles)

        display_skill_analysis(analysis)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
def providers():
    """Show configured AI providers."""
    config = get_config()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Active")

    providers_info = [
        ("anthropic", bool(config.anthropic.api_key)),
        ("openai", bool(config.openai.api_key)),
        ("opencode", bool(config.opencode.base_url)),
    ]

    for name, has_key in providers_info:
        status = "[green]Configured[/green]" if has_key else "[yellow]Not configured[/yellow]"
        active = "[bold green]✓[/bold green]" if config.active_provider == name else ""
        table.add_row(name, status, active)

    console.print(table)
    console.print(f"\nActive provider: [bold]{config.active_provider}[/bold]")


@main.command()
@click.argument("index", type=int)
@click.option(
    "--profile",
    type=click.Path(exists=True, path_type=Path),
    help="Path to profile JSON file",
)
@click.option(
    "--plan",
    is_flag=True,
    help="Include full action plan (before_applying, cover_letter, interview_prep)",
)
def advise(index: int, profile: Path | None, plan: bool):
    """Get AI coaching for job number INDEX from your last search."""
    job = load_job_at_index(index)
    if job is None:
        console.print(
            f"[red]No job at index {index}.[/red] "
            "Run [bold]job-scout search[/bold] first, then use the number shown next to each result."
        )
        sys.exit(1)

    console.print(f"\n[bold]Advising on:[/bold] {job.title} at {job.company}\n")

    config = get_config()
    if profile:
        try:
            user_profile = ProfileParser.load_profile(profile)
        except Exception as e:
            console.print(f"[red]Error loading profile:[/red] {e}")
            sys.exit(1)
    else:
        default_profile = Path("My Instroduction/aniket_profile.json")
        if default_profile.exists():
            user_profile = ProfileParser.load_profile(default_profile)
        else:
            from jobscout.profile import UserProfile
            user_profile = UserProfile()

    try:
        provider = get_provider(config)

        with console.status("[bold green]Analyzing resume fit..."):
            resume_advisor = ResumeAdvisor(provider)
            edits = resume_advisor.suggest_edits(user_profile, job)

        with console.status("[bold green]Analyzing requirements..."):
            req_analyzer = RequirementsAnalyzer(provider)
            report = req_analyzer.analyze(user_profile, job)

        with console.status("[bold green]Generating coaching advice..."):
            coach = ApplicationCoach(provider)
            advice = coach.advise(user_profile, job, include_plan=plan)

        display_resume_edits(edits)
        display_requirements_report(report)
        display_coach_advice(advice)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
