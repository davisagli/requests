"""Unit tests for the requests.redirects module and it's classes."""
import itertools
import typing as t

import pytest

from requests import models
from requests import redirects


def config(**kwargs) -> t.Dict[str, t.Any]:
    """Create a config dictionary/obj for Decision Engine."""
    kwargs.setdefault("allow_redirects", True)
    kwargs.setdefault("max_redirects", 5)
    return kwargs


@pytest.mark.parametrize(
    "status_code",
    itertools.chain(
        filter(lambda x: x not in models.REDIRECT_STATI, range(200, 600))
    ),
)
def test_fails_early_on_a_non_redirect(status_code):
    """Verify we bail if it's not a 301, 302, 303, 307, or 308."""
    eng = redirects.RedirectDecisionEngine(config=config())
    resp = models.Response()
    resp.status_code = status_code

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is False
    assert decision.reason is redirects.Decision.Reason.NO_REDIRECT_DETECTED


def test_max_redirects():
    """Ensure we don't exceed the maximum number of redirect follows."""
    eng = redirects.RedirectDecisionEngine(config=config(max_redirects=5))
    resp = models.Response()
    resp.status_code = 302
    resp.history = list(
        range(5)
    )  # Fake a history with 5 other responses easily

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is False
    assert decision.reason is redirects.Decision.Reason.TOO_MANY_REDIRECTS


def test_disabled_redirects():
    """Ensure we don't follow redirects if the user doesn't want us to."""
    eng = redirects.RedirectDecisionEngine(
        config=config(allow_redirects=False)
    )
    resp = models.Response()
    resp.status_code = 302

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is False
    assert decision.reason is redirects.Decision.Reason.USER_DISABLED_REDIRECTS


@pytest.mark.parametrize(
    "from_url,location_header,expected",
    [
        (
            "https://example.com",
            "//example.com/404",
            "https://example.com/404",
        ),
        (
            "https://example.com/#fragment",
            "//example.com/404",
            "https://example.com/404#fragment",
        ),
        (
            "https://example.com/#fragment",
            "/404",
            "https://example.com/404#fragment",
        ),
        (
            "https://example.com/#fragment",
            "/404",
            "https://example.com/404#fragment",
        ),
    ],
)
def test_redirecting_gets_correct_url(from_url, location_header, expected):
    """Verify we munge URLs correctly as part of redirection."""
    eng = redirects.RedirectDecisionEngine(config=config(max_redirects=5))
    resp = models.Response()
    resp.request = models.PreparedRequest()
    resp.request.method = "GET"  # This doesn't matter as much
    resp.request.headers = {}
    resp.status_code = 302
    resp.url = resp.request.url = from_url
    resp.headers["Location"] = location_header

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is True
    assert decision.was_a_redirect() is True
    assert decision.redirect_url == expected
