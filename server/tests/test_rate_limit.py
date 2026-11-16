import pytest

from app.api.rate_limit import RateLimiter


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_a_caller_is_allowed_up_to_the_limit_and_refused_after_it():
    limiter = RateLimiter(limit=3, window_seconds=60, clock=Clock())
    assert [limiter.allow("1.2.3.4") for _ in range(4)] == [True, True, True, False]


def test_each_caller_has_its_own_count():
    limiter = RateLimiter(limit=1, window_seconds=60, clock=Clock())
    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("5.6.7.8") is True
    assert limiter.allow("1.2.3.4") is False


def test_the_count_starts_again_in_the_next_window():
    clock = Clock(1000.0)  # window [960, 1020)
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    assert limiter.allow("1.2.3.4") is True
    clock.now = 1019.9
    assert limiter.allow("1.2.3.4") is False
    clock.now = 1020.0
    assert limiter.allow("1.2.3.4") is True


def test_retry_after_is_the_whole_seconds_left_in_the_window():
    clock = Clock(1000.0)
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    assert limiter.retry_after() == 20
    clock.now = 1019.5
    assert limiter.retry_after() == 1


def test_when_too_many_callers_are_tracked_new_ones_are_refused_but_known_ones_keep_their_count():
    limiter = RateLimiter(limit=2, window_seconds=60, clock=Clock(), max_callers=2)
    assert limiter.allow("a") and limiter.allow("b")
    assert limiter.allow("c") is False
    assert limiter.allow("a") is True
    assert limiter.allow("a") is False


def test_a_full_table_empties_in_the_next_window():
    clock = Clock(1000.0)
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock, max_callers=1)
    limiter.allow("a")
    assert limiter.allow("b") is False
    clock.now = 1020.0
    assert limiter.allow("b") is True


def test_reset_forgets_every_count():
    limiter = RateLimiter(limit=1, window_seconds=60, clock=Clock())
    limiter.allow("a")
    limiter.reset()
    assert limiter.allow("a") is True


@pytest.mark.parametrize("limit, window", [(0, 60), (1, 0)])
def test_a_limit_or_window_that_allows_nothing_is_a_mistake(limit, window):
    with pytest.raises(ValueError):
        RateLimiter(limit=limit, window_seconds=window)
