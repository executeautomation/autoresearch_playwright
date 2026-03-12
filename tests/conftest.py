"""
Pytest configuration for AutonomousTester.

The agent may add shared fixtures here (e.g. authenticated page, logged-in
context, per-test network mocks). Keep fixtures focused and reusable.

Playwright browser/context/page fixtures (browser, context, page) are
provided automatically by pytest-playwright — do not redefine them.
"""

import pytest


# ---------------------------------------------------------------------------
# Browser context configuration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Global browser context settings applied to every test.
    Extend this fixture if you need cookies, HTTP auth, or custom headers.
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,          # allow self-signed certs in dev
        "locale": "en-US",
        "timezone_id": "America/New_York",
    }


# ---------------------------------------------------------------------------
# Agent-defined shared fixtures go below
# ---------------------------------------------------------------------------

# Example (uncomment and adapt when you have a login flow):
#
# @pytest.fixture
# def authenticated_page(page, base_url):
#     """Return a page that is already logged in."""
#     page.goto(f"{base_url}/login")
#     page.get_by_label("Username").fill("testuser")
#     page.get_by_label("Password").fill("testpass")
#     page.get_by_role("button", name="Sign in").click()
#     page.wait_for_url("**/dashboard")
#     return page
