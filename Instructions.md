# Agent Instructions — AutonomousTester

Follow these steps **in order** every time you run the autonomous testing loop.

---

## Step 1 — Read Context Files

Before doing anything, read these files:

- `program.md` — full agent instructions and rules
- `runner.py` — understand what it runs and what it logs (do not edit)
- `explorer.py` — understand what it crawls and what it produces (do not edit)
- `tests/test_suite.py` — your **only** editable file; read the current state
- `results.tsv` — read all previous runs to understand current coverage_score

---

## Step 2 — Set the Target URL

Open `tests/test_suite.py` and set `TARGET_URL` to the application you want to test:

```python
TARGET_URL = "http://your-app-url.com"
```

> This is required. If `TARGET_URL` is still `https://example.com`, the tests will run against the wrong app.

---

## Step 3 — Explore the Application

Run the explorer to crawl the app and build a site map:

```bash
cd AutonomousTester
uv run explorer.py <TARGET_URL> --depth 2 --max-pages 25
```

This produces:
- `site_map.json` — all pages, links, buttons, forms, headings discovered
- `snapshots/` — screenshots of each page

> The explorer does NOT write any tests. It only collects information for you to use.

After it finishes, read `site_map.json` to understand:
- What pages exist
- What forms, buttons, and inputs are on each page
- Which pages require authentication

---

## Step 4 — Run Baseline First (Important)

Before writing any new tests, run the existing tests to establish a baseline:

```bash
uv run runner.py --description "baseline"
```

This tells you the starting `coverage_score`. Every subsequent run should improve it.

---

## Step 5 — Plan Your Tests

Based on `site_map.json`, plan tests for:

1. **Public pages** — do they load? Do they show the right content?
2. **Forms** — valid input, invalid input, empty submission, error messages
3. **Authentication** — login with valid creds, login with wrong creds, logout
4. **Protected pages** — redirect to login when not authenticated
5. **Navigation** — links go to the right pages
6. **User flows** — multi-step journeys (e.g. login → navigate → perform action → verify result)

---

## Step 6 — Write Tests in test_suite.py

Edit `tests/test_suite.py` only. Add test functions following these rules:

```python
def test_<page>_<behaviour>_<condition>(page: Page):
    """Clear description of what this test checks."""
    page.goto(f"{TARGET_URL}/path")
    expect(page.get_by_role("heading", name="Expected Title")).to_be_visible()
```

**Rules:**
- Use `get_by_role`, `get_by_label`, `get_by_text` — not CSS classes or XPath
- Use `expect()` assertions — they auto-wait; never use `time.sleep()`
- Every test must be independent — no shared state between tests
- If a test needs login, call the `_login(page)` helper at the start
- Do not skip failing tests with `@pytest.mark.skip` — fix them or remove them

**If the app requires login, add a helper at the top of the file:**

```python
def _login(page: Page) -> None:
    page.goto(f"{TARGET_URL}/Account/Login")
    page.locator("input[name='UserName']").fill("admin")
    page.locator("input[name='Password']").fill("password")
    page.get_by_role("button", name=re.compile(r"sign in", re.I)).click()
    page.wait_for_url(re.compile(r"(?!.*/Login).*"), timeout=10_000)
```

---

## Step 7 — Run the Tests

```bash
uv run runner.py --description "brief description of what you tested"
```

This will:
1. Run all tests in `tests/test_suite.py` with headless Chromium
2. Print a summary with `passed`, `failed`, `coverage_score`
3. Save failure screenshots to `snapshots/`
4. Append a row to `results.tsv`

---

## Step 8 — Analyze Results

After the run:

1. Check the printed summary — how many passed vs failed?
2. For each **failed** test:
   - Read the error message carefully
   - Look at the screenshot in `snapshots/` — what does the page actually look like?
   - Common causes:
     - **Strict mode violation** — your selector matched multiple elements → use `.first` or be more specific
     - **Timeout** — element not found → check the selector, or the page needs login
     - **Wrong text** — the page content differs from what you expected → update the assertion
3. Fix the failures in `test_suite.py`

---

## Step 9 — Loop Until coverage_score == 1.0

Repeat Steps 6 → 7 → 8 until all tests pass:

```
coverage_score = passed / total

Goal: coverage_score == 1.0
```

Each iteration should either:
- Fix failing tests, **or**
- Add new tests for uncovered pages/flows AND keep existing tests passing

If a run makes things worse (coverage_score drops for no good reason), revert:

```bash
git checkout tests/test_suite.py
```

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `uv run explorer.py <URL> --depth 2 --max-pages 25` | Crawl app → `site_map.json` + screenshots |
| `uv run runner.py --description "..."` | Run all tests → print results + append to `results.tsv` |
| `cat results.tsv` | See all previous runs |
| `cat site_map.json` | See all discovered pages and elements |
| `ls snapshots/` | See failure screenshots |
| `git checkout tests/test_suite.py` | Revert test file to last commit |

## File Roles

| File | Role | Editable? |
|------|------|-----------|
| `tests/test_suite.py` | All Playwright tests | **YES — only file to edit** |
| `tests/conftest.py` | Shared browser fixtures | Yes (minor additions only) |
| `explorer.py` | BFS web crawler | No |
| `runner.py` | Test executor + TSV logger | No |
| `site_map.json` | Crawler output | Auto-generated |
| `results.tsv` | Run history | Auto-generated |
| `snapshots/` | Failure screenshots | Auto-generated |
