#!/usr/bin/env python3
"""
SCOUT - Public Professional Profile Finder

CLI for public professional-context research.
It does not bypass logins, CAPTCHAs, paywalls, or robots.txt rules.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

USER_AGENT = "SCOUT-PublicProfileFinder/1.0"
TIMEOUT = 15
MAX_RESULTS_PER_QUERY = 10
MAX_PAGES_TO_EXTRACT = 5

BLOCKED_DOMAINS = {
    "whitepages.com",
    "spokeo.com",
    "beenverified.com",
    "truthfinder.com",
    "intelius.com",
    "radaris.com",
    "fastpeoplesearch.com",
    "peekyou.com",
}

SENSITIVE_TERMS = {
    "phone",
    "mobile",
    "email address",
    "home address",
    "residential address",
    "family",
    "wife",
    "husband",
    "children",
    "password",
    "salary",
    "bank",
    "credit card",
    "ssn",
    "social security",
}


def clean_text(text, limit=3500):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


def is_allowed_url(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")

    if parsed.scheme not in {"http", "https"} or not host:
        return False

    for blocked in BLOCKED_DOMAINS:
        if host == blocked or host.endswith("." + blocked):
            return False

    return True


def robots_allows(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        response = requests.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )

        if response.status_code == 404:
            return True

        if response.status_code != 200:
            return False

        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)

    except requests.RequestException:
        return False


def fetch_public_page(url):
    if not is_allowed_url(url) or not robots_allows(url):
        return None

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

        if "text/html" not in response.headers.get("content-type", "").lower():
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "noscript", "svg", "nav",
            "footer", "header", "form", "iframe"
        ]):
            tag.decompose()

        title = ""
        if soup.title:
            title = clean_text(soup.title.get_text(" ", strip=True), 300)

        text = clean_text(soup.get_text(" ", strip=True))

        if len(text) < 100:
            return None

        return {
            "url": response.url,
            "title": title,
            "text_preview": text,
        }

    except requests.RequestException:
        return None


def search_public_sources(name, context):
    base_query = f'"{name}" {context}'.strip()

    queries = [
        f"{base_query} professional profile",
        f"{base_query} portfolio company bio",
        f"{base_query} conference interview article",
        f"{base_query} github publications",
        f'site:linkedin.com/in "{name}" {context}',
        f'site:linkedin.com/pub "{name}" {context}',
        f'site:instagram.com "{name}" {context}',
    ]

    seen_urls = set()
    results = []

    with DDGS() as ddgs:
        for query in queries:
            try:
                for item in ddgs.text(
                    query,
                    max_results=MAX_RESULTS_PER_QUERY
                ):
                    url = item.get("href") or item.get("url")

                    if (
                        not url
                        or url in seen_urls
                        or not is_allowed_url(url)
                    ):
                        continue

                    seen_urls.add(url)

                    results.append({
                        "query": query,
                        "title": clean_text(item.get("title", ""), 300),
                        "url": url,
                        "snippet": clean_text(item.get("body", ""), 900),
                    })

            except Exception as error:
                console.print(
                    f"[yellow]Search warning:[/yellow] {error}"
                )

    return results


def validate_query(name, context):
    query_check = f"{name} {context}".lower()
    return not any(term in query_check for term in SENSITIVE_TERMS)


def render_logo():
    """Display the requested ASCII spider beside SCOUT."""
    spider = [



        r"               ,:' ,d$$??::.     ,, d?",
        r"             J'  ,$$$Z$$Ii:.   ª°",
        r"            d7  j$$Z$$Sii:·. d'",
        r"            ?p  SS$$$S?i:·. $'",
        r"             °:?$Z$8S?:'  .$'",
        r"           dp,  `ª?S?i:' ,°",
        r"          ? ¨ª?,oS%.¨   ·",
        r"       ,g%¬,.j$$$?i:·,iS$jp _",
        r"      ·?  ` 7ª?Si:' ¬.       ¨¨`ª?p,¬·.",
        r"    j7   ,p:jb¨47·,j`47'",
        r"  d'  .47'  ?¨¨?  d7'   `$:",
        r" ?  j:'     `  '  `j?     `jL",
        r" :  :ª'             sL       `?k",
        r" ·  :?               `jb        ¨j,_",
        r"    j'                  ?k         `ª:,",
        r"    i                     `?.           \"·",
        r"    :                        :k",
        r"    ·                         `°.",
        r"                                 `·",
    ]

    scout = [


    
        r"███████╗ ██████╗ ██████╗ ██╗   ██╗████████╗",
        r"██╔════╝██╔════╝██╔═══██╗██║   ██║╚══██╔══╝",
        r"███████╗██║     ██║   ██║██║   ██║   ██║   ",
        r"╚════██║██║     ██║   ██║██║   ██║   ██║   ",
        r"███████║╚██████╗╚██████╔╝╚██████╔╝   ██║   ",
        r"╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   ",
        r"",
        r"                    SCOUT",
        r"        Public Professional Intelligence",
        r"",
        r"        Search Engine      : READY",
        r"        Page Extractor     : READY",
        r"        Robots Policy      : ENABLED",
        r"        Sensitive Filter   : ENABLED",
        r"        Report Format      : JSON",
    ]

    left_width = max(len(line) for line in spider) + 5

    for i in range(max(len(spider), len(scout))):
        left = spider[i] if i < len(spider) else ""
        right = scout[i] if i < len(scout) else ""
        console.print(
            Text(left.ljust(left_width) + right, style="bright_cyan")
        )

    console.print()


def show_banner():
    render_logo()

    console.print(
        Panel(
            Text(
                "Discover • Collect • Verify • Report",
                style="bold bright_cyan",
            ),
            border_style="cyan",
            box=box.SIMPLE,
            padding=(0, 1),
            expand=False,
        )
    )

    console.print(
        "[dim]Public web sources only • robots.txt respected • "
        "sensitive personal-data queries blocked[/dim]\n"
    )


def show_status():
    table = Table(
        title="SCOUT STATUS",
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
    )
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Purpose")

    table.add_row("Search Engine", "[green]READY[/green]",
                  "Public web search via DDGS")
    table.add_row("Page Extractor", "[green]READY[/green]",
                  "Requests + BeautifulSoup")
    table.add_row("Robots Policy", "[green]ENABLED[/green]",
                  "Checks robots.txt before extraction")
    table.add_row("Sensitive Filter", "[green]ENABLED[/green]",
                  "Blocks sensitive-personal-data queries")
    table.add_row("Report Format", "[green]JSON[/green]",
                  "Structured investigation report")

    console.print(table)


def display_search_results(results):
    if not results:
        console.print(
            Panel(
                "No public search results were returned.",
                title="RESULT",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title=f"SEARCH RESULTS ({len(results)})",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )

    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Title", style="bold", max_width=38)
    table.add_column("URL", style="blue", max_width=58)
    table.add_column("Snippet", max_width=65)

    for i, result in enumerate(results, 1):
        table.add_row(
            str(i),
            result["title"] or "Untitled",
            result["url"],
            result["snippet"] or "No snippet",
        )

    console.print(table)


def extract_pages(results):
    extracted = []

    console.print(
        Panel(
            f"Extracting up to {MAX_PAGES_TO_EXTRACT} allowed public pages...",
            title="PAGE EXTRACTION",
            border_style="cyan",
        )
    )

    for i, result in enumerate(results[:MAX_PAGES_TO_EXTRACT], 1):
        console.print(f"[cyan][{i}/{min(len(results), MAX_PAGES_TO_EXTRACT)}][/cyan] "
                      f"{result['url']}")

        page = fetch_public_page(result["url"])

        if page:
            extracted.append({
                "search_query": result["query"],
                "search_title": result["title"],
                "search_snippet": result["snippet"],
                **page,
            })
            console.print("  [green]✓ Extracted[/green]")
        else:
            console.print(
                "  [yellow]• Skipped "
                "(blocked, non-HTML, unavailable, or robots.txt)[/yellow]"
            )

    return extracted


def run_search(name, context, output_path, search_only=False):
    if not validate_query(name, context):
        console.print(
            Panel(
                "Sensitive-personal-data query detected. "
                "SCOUT only supports legitimate public professional research.",
                title="BLOCKED",
                border_style="red",
            )
        )
        return

    console.print(
        Panel(
            f"[bold]Name:[/bold] {name}\n"
            f"[bold]Context:[/bold] {context or 'None'}\n"
            f"[bold]Mode:[/bold] "
            f"{'Search only' if search_only else 'Search + extraction'}",
            title="INVESTIGATION",
            border_style="cyan",
        )
    )

    console.print("\n[cyan]Searching public professional sources...[/cyan]")

    results = search_public_sources(name, context)

    console.print(
        f"[green]Found {len(results)} public search results.[/green]\n"
    )

    display_search_results(results)

    extracted = [] if search_only else extract_pages(results)

    report = {
        "tool": "SCOUT",
        "version": "1.0",
        "subject": name,
        "context": context,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notice": (
            "Public professional-context research only. "
            "Verify every claim using the source URL."
        ),
        "search_results_found": results,
        "sources_extracted": extracted,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    summary = Table(
        title="REPORT SUMMARY",
        box=box.ROUNDED,
        border_style="green",
    )
    summary.add_column("Metric", style="bold")
    summary.add_column("Value", style="green")
    summary.add_row("Search results", str(len(results)))
    summary.add_row("Pages extracted", str(len(extracted)))
    summary.add_row("Report", str(output_path))

    console.print()
    console.print(summary)


def interactive_mode():
    while True:
        show_banner()

        menu = Table(
            title="MAIN MENU",
            box=box.ROUNDED,
            border_style="cyan",
        )
        menu.add_column("Option", style="bold cyan", width=10)
        menu.add_column("Action", style="bold")
        menu.add_row("1", "Find public professional profile")
        menu.add_row("2", "Search only (no page extraction)")
        menu.add_row("3", "Show status")
        menu.add_row("4", "Exit")

        console.print(menu)

        choice = Prompt.ask(
            "\n[bold cyan]SCOUT[/bold cyan]",
            choices=["1", "2", "3", "4"],
            default="1",
        )

        if choice == "4":
            console.print("\n[cyan]SCOUT session closed.[/cyan]")
            break

        if choice == "3":
            show_status()
            Prompt.ask("\nPress Enter to return", default="")
            continue

        name = Prompt.ask("\nFull name").strip()
        context = Prompt.ask("Professional context", default="").strip()

        if not name:
            console.print("[red]Name cannot be empty.[/red]")
            continue

        if not validate_query(name, context):
            console.print("[red]Sensitive-personal-data query blocked.[/red]")
            continue

        default_output = (
            f"profile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        output = Prompt.ask(
            "Output JSON file",
            default=default_output,
        ).strip()

        search_only = choice == "2"

        if not search_only:
            extract = Confirm.ask(
                "Extract allowed public pages?",
                default=True,
            )
            search_only = not extract

        run_search(name, context, output, search_only)

        if not Confirm.ask("\nRun another search?", default=True):
            console.print("\n[cyan]SCOUT session closed.[/cyan]")
            break


def main():
    parser = argparse.ArgumentParser(
        description="SCOUT - Public Professional Profile Finder"
    )

    parser.add_argument(
        "name",
        nargs="?",
        help='Full name, for example: "Ada Lovelace"',
    )
    parser.add_argument(
        "--context",
        default="",
        help="Professional context such as role, company, or city",
    )
    parser.add_argument(
        "--output",
        default="profile_report.json",
        help="JSON report filename",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Show search results without extracting pages",
    )

    args = parser.parse_args()

    if args.name:
        show_banner()
        run_search(
            args.name,
            args.context,
            args.output,
            args.search_only,
        )
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
