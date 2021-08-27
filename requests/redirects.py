"""Redirect logic and handling in its own stand-alone class."""
import enum
import typing as t

from . import models


class Decision:
    # TODO(sigmavirus24): Are there other reasons we'd want to not allow a
    # redirect?
    class Reason(enum.Enum):
        TOO_MANY_REDIRECTS = "tmr"
        NO_REDIRECT_DETECTED = "nrd"

    def __init__(
        self,
        *,
        allow_redirect: bool,
        reason: t.Optional[Reason] = None,
        **kwargs
    ):
        self.allow_redirect = allow_redirect
        self.reason = reason


class RedirectDecisionEngine:
    def __init__(self, config):
        self._config = config

    @property
    def max_redirect_limit(self) -> int:
        return self._config["max_redirects"]

    def decision_for(self, response: models.Response) -> Decision:
        if response.status_code not in models.REDIRECT_STATI:
            return Decision(
                allow_redirect=False,
                reason=Decision.Reason.NO_REDIRECT_DETECTED,
            )
        if len(response.history) >= self.max_redirect_limit:
            return Decision(
                allow_redirect=False, reason=Decision.Reason.TOO_MANY_REDIRECTS
            )
        return Decision(allow_redirect=True)
