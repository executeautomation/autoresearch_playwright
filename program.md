# AutonomousTester

This is an autonomous UI testing agent powered by Playwright. Inspired by [autoresearch](../README.md), the idea is the same: let the AI agent explore a web application, write tests, run them, analyze the results, and loop forever — without human intervention.

## How it works

The repo has three files that matter:

- **`explorer.py`** — fixed utility. Crawls a web app, takes screenshots, builds `site_map.json`. Do not modify.
- **`runner.py`** — fixed test runner. Executes all tests, logs results to `results.tsv`, saves screenshots to `snapshots/`. Do not modify.
- **`tests/test_suite.py`** — **the only file you edit.** Add Playwright test functions here.
- **`program.md`** — this file. Agent instructions. Edited by the human to guide research direction.

The metric is **coverage_score** — the ratio of passing tests to total tests. Higher is better. The goal is to write more tests, make them pass, and cover more of the application's functionality.

---

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar12`). The branch `autotester/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autotester/<tag>` from current master.
3. **Read the in-scope files**: Read these files for full context:
   - `program.md` — this file.
   - `explorer.py` — read-only. Understand what it produces.
   - `runner.py` — read-only. Understand what it runs and logs.
   - `tests/test_suite.py` — your editing surface. Read the current state.
4. **Set the target URL**: Edit `TARGET_URL` in `tests/test_suite.py` to point to the application under test.
5. **Install Playwright browsers** (one-time): `uv run playwright install chromium`
6. **Explore the app**: Run the explorer to build a site map:
   ```
   uv run explorer.py <TARGET_URL> --depth 2 --max-pages 20 > explore.log 2>&1
   ```
   Then read `site_map.json` and `explore.log` to understand the app structure.
7. **Initialize results.tsv**: It will be auto-created on the first `runner.py` run.
8. **Confirm and go**: Confirm the target URL, site map looks good, and kick off the loop.

---

## Experimentation

Each test run executes with a fixed invocation: `uv run runner.py`

**What you CAN do:**
- Modify `tests/test_suite.py` — this is the **only** file you edit. Everything is fair game:
  - Add new test functions for any page, interaction, or user flow.
  - Add Page Object Model classes for maintainability.
  - Add helper fixtures in `tests/conftest.py` (you may also edit this file).
  - Test navigation, forms, modals, API responses, visual elements, error states.
  - Test keyboard navigation, responsive behavior, accessibility attributes.

**What you CANNOT do:**
- Modify `runner.py` or `explorer.py`. They are fixed infrastructure.
- Use `time.sleep()` or `page.wait_for_timeout()`. Use Playwright's built-in auto-waiting.
- Skip failing tests with `@pytest.mark.skip` as a cheat. Fix them or remove them.
- Add hard-coded CSS class selectors as sole identifiers. Use ARIA roles, labels, text.
- Install new packages or change `pyproject.toml` (it is fixed).

**The goal is simple: maximize coverage_score and minimize failed tests.**

Strategy:
- Explore first — understand pages, forms, navigation, dynamic content.
- Start broad — write one test per page/section to establish a baseline.
- Go deep — test each interactive element: buttons, forms, modals, links.
- Cover edge cases — empty inputs, invalid data, error messages, 404s.
- Cover flows — multi-step user journeys (e.g. fill form → submit → confirm result).

**Simplicity criterion**: All else being equal, simpler is better. A test that's overly brittle or relies on implementation details is not worth keeping. A clean, readable test that covers a real user scenario is gold. Remove tests that constantly flake.

**The first run**: Your very first run should always be with the baseline tests unchanged, to establish the starting coverage_score.

---

## Output format

Once `runner.py` finishes, it prints a summary like this:

```
---
total_tests:    12
passed:         10
failed:         2
errors:         0
duration_s:     45.3
coverage_score: 0.8333
status:         keep
---
Snapshots saved to: snapshots/
Results logged to:  results.tsv
```

You can extract the key metrics from the log file:

```bash
grep "^passed:\|^failed:\|^coverage_score:\|^status:" run.log
```

Screenshots of failing tests are saved to `snapshots/`. Always read them — they tell you what the page actually looks like when a test fails.

---

## Logging results

When an experiment is done, the runner auto-logs it to `results.tsv` with status `auto`. **You must update the description** to something meaningful:

```
results.tsv
```

The TSV has a header row and 8 columns (tab-separated — no commas in descriptions):

```
commit	passed	failed	errors	duration_s	coverage_score	status	description
```

1. `commit` — short git hash (7 chars)
2. `passed` — number of passing tests
3. `failed` — number of failing tests
4. `errors` — number of test collection errors
5. `duration_s` — total run time in seconds
6. `coverage_score` — ratio of passed/total (e.g. 0.8333)
7. `status` — `keep`, `discard`, or `crash`
8. `description` — short human-readable description of what this run tested

**Status rules:**
- `keep` — coverage_score improved or held steady with more tests added.
- `discard` — coverage_score dropped without a good reason. Revert with `git checkout tests/test_suite.py`.
- `crash` — runner itself crashed (collection error, import error, etc.).

Example:

```
commit	passed	failed	errors	duration_s	coverage_score	status	description
a1b2c3d	2	0	0	8.2	1.0000	keep	baseline homepage and content
b2c3d4e	8	1	0	22.5	0.8889	keep	add nav links + form submission tests
c3d4e5f	8	3	0	25.1	0.7273	discard	button tests too brittle — reverted
d4e5f6g	12	0	0	34.8	1.0000	keep	fix selectors + add modal and error tests
```

---

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autotester/mar12`).

**LOOP FOREVER:**

1. Look at the git state: current branch, last commit, last `results.tsv` row.
2. Read `site_map.json` — identify untested pages, elements, or flows.
3. Read the current `tests/test_suite.py` — understand what is already covered.
4. Add or improve tests in `tests/test_suite.py` based on your analysis.
5. `git add tests/test_suite.py && git commit -m "<short description>"`
6. Run the experiment:
   ```bash
   uv run runner.py --description "your description here" > run.log 2>&1
   ```
7. Read results:
   ```bash
   grep "^passed:\|^failed:\|^coverage_score:\|^status:" run.log
   ```
8. Check failure screenshots: open `snapshots/*.png` for failing tests.
9. Update `results.tsv` — make sure description is meaningful, not "auto".
10. Decide: keep or discard. If discard, `git checkout tests/test_suite.py`.
11. Plan the next experiment. What is untested? What failed? What can be improved?

**Re-explore when needed**: If the app has dynamic content or new pages you haven't mapped, re-run:
```bash
uv run explorer.py <TARGET_URL> --depth 3 > explore.log 2>&1
```

---

## Tips for good tests

- **Prefer role/label selectors**: `page.get_by_role("button", name="Submit")` over `page.locator(".btn-submit")`
- **Use `expect()` assertions**: they auto-wait. Avoid manual waits.
- **Test real flows**: don't just check elements exist — interact with them.
- **Test error states**: submit empty forms, enter invalid data, navigate to 404s.
- **Use fixtures**: if multiple tests share setup (login, navigation), extract to a pytest fixture.
- **Name tests clearly**: `test_login_form_shows_error_on_empty_submit` is better than `test_form`.
