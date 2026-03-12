# How To Run AutonomousTester

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- A web application URL to test against

Install `uv` if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Step 1 — Install dependencies

```bash
cd AutonomousTester
uv sync
```

---

## Step 2 — Install the Playwright browser

```bash
uv run playwright install chromium
```

---

## Step 3 — Set your target URL

Open `tests/test_suite.py` and change the `TARGET_URL` at the top:

```python
TARGET_URL = "https://your-app-url.com"
```

---

## Step 4 — Explore the application (optional but recommended)

This crawls the app, takes screenshots, and writes `site_map.json` so you (or the agent) can see what pages and elements exist before writing tests.

```bash
uv run explorer.py https://your-app-url.com
```

Optional flags:
```bash
uv run explorer.py https://your-app-url.com --depth 3 --max-pages 30
```

Output:
- `site_map.json` — structured page inventory
- `snapshots/explore_*.png` — screenshot of every visited page

---

## Step 5 — Run the tests

```bash
uv run runner.py --description "baseline"
```

This runs all tests in `tests/test_suite.py`, prints a summary, and appends a row to `results.tsv`.

Expected output:
```
---
total_tests:    2
passed:         2
failed:         0
errors:         0
duration_s:     3.8
coverage_score: 1.0000
status:         keep
---
Snapshots saved to: snapshots/
Results logged to:  results.tsv
```

---

## Step 6 — Add more tests (the autonomous loop)

Edit `tests/test_suite.py` — this is the **only file you (or the agent) modify**. Add new `def test_*` functions to cover more pages, forms, and user flows.

Then run again:
```bash
uv run runner.py --description "add nav and form tests"
```

Check `results.tsv` to track progress over time.

---

## Step 7 — Diagnose failures

If tests fail, check the screenshots saved in `snapshots/`:
```
snapshots/<test-name>.png
```

Or read the full test log:
```bash
uv run runner.py > run.log 2>&1
grep "^passed:\|^failed:\|^coverage_score:\|^status:" run.log
```

---

## File reference

| File | Purpose | Edit? |
|---|---|---|
| `tests/test_suite.py` | All Playwright tests | Yes — add tests here |
| `tests/conftest.py` | Shared pytest fixtures | Yes — add shared setup here |
| `explorer.py` | App crawler | No — fixed infrastructure |
| `runner.py` | Test executor + logger | No — fixed infrastructure |
| `program.md` | Full agent instructions | Human edits to guide the agent |
| `results.tsv` | Experiment log (auto-created) | Auto-updated by runner |
| `site_map.json` | App map (auto-created by explorer) | Read-only reference |
