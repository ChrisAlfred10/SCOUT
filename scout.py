
#!/usr/bin/env python3
"""
SCOUT - Public Professional Intelligence Tool
Public professional-profile discovery using multiple search providers.
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

USER_AGENT = "SCOUT-PublicProfileFinder/1.1"
TIMEOUT = 15
MAX_RESULTS_PER_QUERY = 10
MAX_PAGES_TO_EXTRACT = 5

SEARCH_BACKENDS = [
    "google",
    "brave",
    "bing",
    "duckduckgo",
]

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

# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(text, limit=3500):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]

def is_allowed_url(url):
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")

        if parsed.scheme not in {"http", "https"} or not host:
            return False

        for blocked in BLOCKED_DOMAINS:
            if host == blocked or host.endswith("." + blocked):
                return False

        return True

    except Exception:
        return False

def validate_query(name, context):
    query = f"{name} {context}".lower()

    return not any(
        term in query for term in SENSITIVE_TERMS
    )

# ============================================================
# ROBOTS.TXT POLICY
# ============================================================

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
        parser.parse(response.text.splitlines())

        return parser.can_fetch(USER_AGENT, url)

    except requests.RequestException:
        return False

# ============================================================
# PUBLIC PAGE EXTRACTION
# ============================================================

def fetch_public_page(url):

    if not is_allowed_url(url):
        return None

    if not robots_allows(url):
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

        if not is_allowed_url(response.url):
            return None

        if "text/html" not in response.headers.get(
            "content-type", ""
        ).lower():
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "form",
            "iframe",
        ]):
            tag.decompose()

        title = ""

        if soup.title:
            title = clean_text(
                soup.title.get_text(" ", strip=True),
                300,
            )

        text = clean_text(
            soup.get_text(" ", strip=True)
        )

        if len(text) < 100:
            return None

        return {
            "url": response.url,
            "title": title,
            "text_preview": text,
        }

    except requests.RequestException:
        return None

# ============================================================
# SEARCH ENGINE WITH PROVIDER FALLBACK
# ============================================================

def search_one_provider(ddgs, query, backend):

    try:
        results = ddgs.text(
            query,
            region="in-en",
            safesearch="moderate",
            max_results=MAX_RESULTS_PER_QUERY,
            backend=backend,
        )

        return results or []

    except Exception as error:
        console.print(
            f"[dim]  {backend.upper()} unavailable: "
            f"{str(error)[:120]}[/dim]"
        )

        return []

def search_public_sources(name, context):

    base_query = f'"{name}" {context}'.strip()

    queries = [
        f"{base_query} professional profile",
        f"{base_query} portfolio company bio",
        f"{base_query} conference interview article",
        f"{base_query} github publications",
        f'site:linkedin.com/in "{name}" {context}',
        f'site:github.com "{name}" {context}',
    ]

    seen_urls = set()
    results = []

    try:
        with DDGS(timeout=TIMEOUT) as ddgs:

            for query in queries:

                console.print(
                    f"\n[white]Query:[/white] {query}"
                )

                query_results = []

                for backend in SEARCH_BACKENDS:

                    console.print(
                        f"[dim]Trying {backend.upper()}...[/dim]"
                    )

                    query_results = search_one_provider(
                        ddgs,
                        query,
                        backend,
                    )

                    if query_results:
                        console.print(
                            f"[white]Provider succeeded: "
                            f"{backend.upper()}[/white]"
                        )
                        break

                if not query_results:
                    console.print(
                        "[dim]No results from available providers.[/dim]"
                    )
                    continue

                for item in query_results:

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
                        "title": clean_text(
                            item.get("title", ""),
                            300,
                        ),
                        "url": url,
                        "snippet": clean_text(
                            item.get("body", ""),
                            900,
                        ),
                    })

    except Exception as error:
        console.print(
            f"[white]Search initialization error: "
            f"{str(error)[:200]}[/white]"
        )

    return results

# ============================================================
# ASCII SPIDER + SCOUT LOGO
# ============================================================

def render_logo():

    spider = [
        r"               ,:'   ,d$$??::.     ,, d?",
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
        "",
        "                    SCOUT",
        "        Public Professional Intelligence",
        "",
        "        Search Engine      : READY",
        "        Page Extractor     : READY",
        "        Robots Policy      : ENABLED",
        "        Sensitive Filter   : ENABLED",
        "        Report Format      : JSON",
        "        Search Fallback   : ENABLED",
    ]

    # Center the complete spider + SCOUT artwork.
    left_width = max(len(line) for line in spider) + 5
    right_width = max(len(line) for line in scout)
    artwork_width = left_width + right_width

    left_padding = max(
        0,
        (console.width - artwork_width) // 2
    )

    for i in range(max(len(spider), len(scout))):

        left = spider[i] if i < len(spider) else ""
        right = scout[i] if i < len(scout) else ""

        console.print(
            Text(
                " " * left_padding
                + left.ljust(left_width)
                + right,
                style="white",
            )
        )

    console.print()

def show_banner():

    console.print("\n\n")

    render_logo()

    console.print(
        Panel(
            Text(
                "Discover • Collect • Verify • Report",
                style="bold white",
            ),
            border_style="white",
            box=box.SIMPLE,
            padding=(0, 1),
            expand=False,
        )
    )

    console.print(
        "[dim]SCOUT uses public web sources and respects robots.txt. "
        "Do not use it to collect sensitive personal information.[/dim]\n"
    )

# ============================================================
# STATUS
# ============================================================

def show_status():

    table = Table(
        title="SCOUT STATUS",
        box=box.SIMPLE_HEAVY,
        border_style="white",
    )

    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Purpose")

    table.add_row(
        "Search Engine",
        "READY",
        "Multiple public search providers",
    )

    table.add_row(
        "Search Fallback",
        "ENABLED",
        "Tries another provider after failure",
    )

    table.add_row(
        "Page Extractor",
        "READY",
        "Requests + BeautifulSoup",
    )

    table.add_row(
        "Robots Policy",
        "ENABLED",
        "Checks robots.txt before extraction",
    )

    table.add_row(
        "Sensitive Filter",
        "ENABLED",
        "Blocks sensitive-data queries",
    )

    table.add_row(
        "Report Format",
        "JSON",
        "Structured research report",
    )

    console.print(table)

    console.print(
        "\n[white]Search providers:[/white] "
        + " → ".join(SEARCH_BACKENDS)
    )

# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_search_results(results):

    if not results:

        console.print(
            Panel(
                "No public search results were returned.\n"
                "Check your internet connection or try again later.",
                title="RESULT",
                border_style="white",
            )
        )

        return

    table = Table(
        title=f"SEARCH RESULTS ({len(results)})",
        box=box.ROUNDED,
        border_style="white",
        show_lines=True,
    )

    table.add_column("#", width=4)
    table.add_column("Title", max_width=35)
    table.add_column("URL", max_width=55)
    table.add_column("Snippet", max_width=60)

    for i, result in enumerate(results, 1):

        table.add_row(
            str(i),
            result["title"] or "Untitled",
            result["url"],
            result["snippet"] or "No snippet",
        )

    console.print(table)

# ============================================================
# PAGE EXTRACTION
# ============================================================

def extract_pages(results):

    extracted = []

    console.print(
        Panel(
            f"Extracting up to {MAX_PAGES_TO_EXTRACT} allowed public pages...",
            title="PAGE EXTRACTION",
            border_style="white",
        )
    )

    for i, result in enumerate(
        results[:MAX_PAGES_TO_EXTRACT],
        1,
    ):

        console.print(
            f"\n[white][{i}/{min(len(results), MAX_PAGES_TO_EXTRACT)}]"
            f"[/white] {result['url']}"
        )

        page = fetch_public_page(result["url"])

        if page:

            extracted.append({
                "search_query": result["query"],
                "search_title": result["title"],
                "search_snippet": result["snippet"],
                **page,
            })

            console.print("[white]✓ Extracted[/white]")

        else:

            console.print(
                "[dim]Skipped: blocked, unavailable, "
                "non-HTML, or robots.txt restriction.[/dim]"
            )

    return extracted

# ============================================================
# JSON REPORT
# ============================================================

def save_report(name, context, results, extracted, output):

    report = {
        "tool": "SCOUT",
        "version": "1.1",
        "subject": name,
        "context": context,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notice": (
            "Public professional-context research only. "
            "Verify every claim using its source URL."
        ),
        "search_results_found": results,
        "sources_extracted": extracted,
    }

    output_path = Path(output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path

# ============================================================
# MAIN INVESTIGATION
# ============================================================

def run_search(name, context, output, search_only=False):

    if not validate_query(name, context):

        console.print(
            Panel(
                "Sensitive-personal-data query detected.\n"
                "SCOUT only supports legitimate public professional research.",
                title="BLOCKED",
                border_style="white",
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
            border_style="white",
        )
    )

    console.print(
        "\n[white]Searching public professional sources...[/white]\n"
    )

    results = search_public_sources(name, context)

    console.print(
        f"\n[white]Found {len(results)} public search results.[/white]"
    )

    display_search_results(results)

    if search_only or not results:

        extracted = []

        if not results:
            console.print(
                "\n[dim]Page extraction skipped because "
                "there are no search results.[/dim]"
            )

    else:

        extracted = extract_pages(results)

    report_path = save_report(
        name,
        context,
        results,
        extracted,
        output,
    )

    summary = Table(
        title="REPORT SUMMARY",
        box=box.ROUNDED,
        border_style="white",
    )

    summary.add_column("Metric", style="bold")
    summary.add_column("Value")

    summary.add_row("Search results", str(len(results)))
    summary.add_row("Pages extracted", str(len(extracted)))
    summary.add_row("Report", str(report_path))

    console.print()
    console.print(summary)

# ============================================================
# INTERACTIVE CLI
# ============================================================

def interactive_mode():

    while True:

        show_banner()

        menu = Table(
            title="MAIN MENU",
            box=box.ROUNDED,
            border_style="white",
        )

        menu.add_column("Option", width=10)
        menu.add_column("Action")

        menu.add_row("1", "Find public professional profile")
        menu.add_row("2", "Search only (no page extraction)")
        menu.add_row("3", "Show status")
        menu.add_row("4", "Exit")

        console.print(menu)

        choice = Prompt.ask(
            "\n[bold white]SCOUT[/bold white] [1/2/3/4]",
            choices=["1", "2", "3", "4"],
            default="1",
        )

        if choice == "4":

            console.print(
                "\n[white]SCOUT session closed.[/white]"
            )

            break

        if choice == "3":

            show_status()

            Prompt.ask(
                "\nPress Enter to return",
                default="",
            )

            continue

        name = Prompt.ask(
            "\nFull name"
        ).strip()

        context = Prompt.ask(
            "Professional context",
            default="",
        ).strip()

        if not name:

            console.print(
                "[white]Name cannot be empty.[/white]"
            )

            continue

        if not validate_query(name, context):

            console.print(
                "[white]Sensitive-personal-data query blocked.[/white]"
            )

            continue

        default_output = (
            "profile_report_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".json"
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

        run_search(
            name,
            context,
            output,
            search_only,
        )

        if not Confirm.ask(
            "\nRun another search?",
            default=True,
        ):

            console.print(
                "\n[white]SCOUT session closed.[/white]"
            )

            break

# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="SCOUT - Public Professional Intelligence Tool"
    )

    parser.add_argument(
        "name",
        nargs="?",
        help='Full name, e.g. "Ada Lovelace"',
    )

    parser.add_argument(
        "--context",
        default="",
        help="Professional context such as role or company",
    )

    parser.add_argument(
        "--output",
        default="profile_report.json",
        help="JSON report filename",
    )

    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search without extracting pages",
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

    try:
        main()

    except KeyboardInterrupt:

        console.print(
            "\n[white]SCOUT interrupted by user.[/white]"
        )

        sys.exit(0)