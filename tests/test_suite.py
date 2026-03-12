"""
Playwright test suite — THE ONLY FILE THE AGENT MODIFIES.

Add test functions below. Each function is a self-contained experiment.
The runner executes all of them and reports pass/fail/coverage_score.

Rules:
  - Use role/label selectors (get_by_role, get_by_label, get_by_text).
  - Use expect() assertions — they auto-wait. Never use time.sleep().
  - Every test must be independent: no shared mutable state.
  - Name tests descriptively: test_<page>_<behaviour>_<condition>.
  - Do NOT skip tests with @pytest.mark.skip to hide failures — fix them.

Manual run:
    pytest tests/test_suite.py -v

Via runner (logs to results.tsv):
    uv run runner.py --description "what you tested"
"""

import re

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Target application
# ← Change this to the URL of the application you are testing.
# ---------------------------------------------------------------------------

TARGET_URL = "https://example.com"


# ---------------------------------------------------------------------------
# Baseline tests — establish the starting coverage_score.
# Run these first without modification.
# ---------------------------------------------------------------------------


def test_homepage_loads(page: Page):
    """The homepage responds and renders a non-empty title."""
    page.goto(TARGET_URL)
    expect(page).not_to_have_title("")


def test_page_has_visible_content(page: Page):
    """At least one heading or paragraph is visible on the homepage."""
    page.goto(TARGET_URL)
    content = page.locator("h1, h2, h3, p").first
    expect(content).to_be_visible()


# ---------------------------------------------------------------------------
# Agent adds experiments below this line
# ---------------------------------------------------------------------------

# Hints for the agent:
#
# Navigation example:
#   def test_nav_about_link_navigates(page: Page):
#       page.goto(TARGET_URL)
#       page.get_by_role("link", name="About").click()
#       expect(page).to_have_url(re.compile(r".*/about.*"))
#
# Form example:
#   def test_contact_form_shows_error_on_empty_submit(page: Page):
#       page.goto(f"{TARGET_URL}/contact")
#       page.get_by_role("button", name="Send").click()
#       expect(page.get_by_role("alert")).to_be_visible()
#
# Responsive example:
#   def test_mobile_menu_toggle(page: Page):
#       page.set_viewport_size({"width": 375, "height": 667})
#       page.goto(TARGET_URL)
#       page.get_by_role("button", name=re.compile(r"menu", re.I)).click()
#       expect(page.get_by_role("navigation")).to_be_visible()
#
# API mock example:
#   def test_shows_error_banner_on_api_failure(page: Page):
#       page.route("**/api/data", lambda r: r.fulfill(status=500))
#       page.goto(TARGET_URL)
#       expect(page.get_by_role("alert")).to_contain_text(re.compile(r"error", re.I))
