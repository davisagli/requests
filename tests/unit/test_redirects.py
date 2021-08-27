import itertools

import pytest

from requests import models
from requests import redirects


@pytest.mark.parametrize(
    "status_code",
    itertools.chain(
        range(200, 301), range(304, 307), range(309, 500), range(500, 600)
    ),
)
def test_fails_early_on_a_non_redirect(status_code):
    eng = redirects.RedirectDecisionEngine(config={"max_redirects": 5})
    resp = models.Response()
    resp.status_code = status_code

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is False
    assert decision.reason is redirects.Decision.Reason.NO_REDIRECT_DETECTED


def test_max_redirects():
    eng = redirects.RedirectDecisionEngine(config={"max_redirects": 5})
    resp = models.Response()
    resp.status_code = 302
    resp.history = list(
        range(5)
    )  # Fake a history with 5 other responses easily

    decision = eng.decision_for(resp)
    assert decision.allow_redirect is False
    assert decision.reason is redirects.Decision.Reason.TOO_MANY_REDIRECTS
