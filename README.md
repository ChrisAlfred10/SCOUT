# 🕷️ SCOUT CLI

### Public Professional Profile Research Tool

SCOUT is a Python command-line tool for searching publicly accessible web sources using a person's name and professional context. It displays search results, can extract a limited number of public HTML pages, and saves the collected results in a structured JSON report.

> **Discover. Explore. Verify.**

> **Project status:** Early-stage / experimental. Search results are leads for manual review, not verified identity matches or confirmed facts.

---

## Features

- **Interactive CLI** with a custom spider-inspired startup screen.
- **Name-based search** with optional professional context.
- **Contextual search queries** across several search patterns.
- **Search-only mode** that skips webpage extraction.
- **Limited public-page extraction** using Requests and Beautiful Soup.
- **robots.txt checks** before page extraction.
- **Basic sensitive-query keyword filtering.**
- **JSON reports** containing search results, snippets, source URLs, and extracted page text previews.

## How SCOUT works

1. The user enters a name and optional context.
2. SCOUT builds several search queries.
3. The search provider returns candidate public URLs and snippets.
4. SCOUT displays the candidate results.
5. Unless search-only mode is selected, SCOUT attempts to extract up to five eligible HTML pages.
6. SCOUT writes the search results and extracted page previews to a JSON report.

Search results may be incomplete, outdated, misleading, or refer to a different person with the same name. Always open and verify the original source before relying on a result.

## Technology

- Python
- [DuckDuckGo Search (`ddgs`)](https://pypi.org/project/ddgs/)
- [Requests](https://requests.readthedocs.io/)
- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Rich](https://rich.readthedocs.io/)

---

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SCOUT
```

Use the directory containing `scout.py` if your local folder name differs.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate it

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Usage

### Interactive mode

```bash
python scout.py
```

Follow the menu prompts to start a search, choose search-only mode, view component status, or exit.

### Direct search

```bash
python scout.py "Ada Lovelace"
```

### Search with professional context

```bash
python scout.py "Ada Lovelace" --context "mathematician"
```

### Search without extracting pages

```bash
python scout.py "Ada Lovelace" --context "mathematician" --search-only
```

### Choose a report path

```bash
python scout.py "Ada Lovelace" --context "mathematician" --output reports/ada-report.json
```

---

## Output

SCOUT writes a JSON report containing:

- Tool name and version
- Search subject and context
- Report generation timestamp
- Search queries used
- Search result titles, URLs, and snippets
- Extracted page titles and text previews, when extraction is enabled

Reports may contain personal information from public pages. Store them securely and do not commit them to a public repository.

---

## Responsible use

SCOUT is intended for legitimate research of public professional information.

- Use it only for lawful, appropriate purposes.
- Respect website terms, access restrictions, and robots.txt policies.
- Do not attempt to bypass authentication, CAPTCHAs, paywalls, or other access controls.
- Do not use SCOUT to collect sensitive personal information, stalk, harass, discriminate against, or target individuals.
- Treat results as unverified leads; independently verify identity and claims from original sources.
- Obtain appropriate authorization before conducting research for an organization or another person.

The built-in keyword filter is a basic safeguard, not a complete privacy or safety control. The current implementation should be considered experimental and should not be used for high-impact decisions.

## Limitations

- Search results depend on the external search provider and may change over time.
- Similar names can produce incorrect candidate matches.
- Some websites block automated requests or render content with JavaScript.
- Extraction is limited to a small number of pages and HTML content.
- robots.txt is a crawler policy signal, not permission to access content.
- The current project does not provide reliable identity verification or confidence scoring.

## Roadmap

Potential improvements (not yet implemented):

- [ ] Add automated unit and integration tests.
- [ ] Harden URL validation, DNS/IP checks, and redirect handling.
- [ ] Add request-size limits and safer timeout handling.
- [ ] Improve deduplication and source provenance.
- [ ] Add structured logging and clearer error reporting.
- [ ] Improve privacy safeguards and query validation.
- [ ] Add configurable source selection.
- [ ] Add export formats and report redaction.
- [ ] Refactor into separate modules as the codebase grows.

## Contributing

Contributions, bug reports, and suggestions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Security

Please read [SECURITY.md](SECURITY.md) for responsible vulnerability reporting.

## License

No license has been selected yet. Until a license is added, others do not automatically have permission to reuse, modify, or redistribute this project. Choose a license before presenting the repository as an open-source project.

---

<div align="center">

**🕷️ SCOUT CLI**

*Public-source research. Responsible use. Manual verification.*

</div>
