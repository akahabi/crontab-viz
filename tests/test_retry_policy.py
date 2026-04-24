"""Tests for crontab_viz.retry_policy."""
from datetime import datetime, timedelta

import pytest

from crontab_viz.retry_policy import (
    RetryPolicy,
    RetryPolicyError,
    RetryState,
    build_retry_registry,
    record_attempt,
    should_retry,
)


# ---------------------------------------------------------------------------
# RetryPolicy validation
# ---------------------------------------------------------------------------

def test_retry_policy_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 3
    assert p.interval_seconds == 60


def test_retry_policy_invalid_attempts():
    with pytest.raises(RetryPolicyError):
        RetryPolicy(max_attempts=0)


def test_retry_policy_invalid_interval():
    with pytest.raises(RetryPolicyError):
        RetryPolicy(interval_seconds=0)


# ---------------------------------------------------------------------------
# should_retry
# ---------------------------------------------------------------------------

def test_should_retry_first_attempt():
    policy = RetryPolicy(max_attempts=3, interval_seconds=30)
    state = RetryState()
    assert should_retry(state, policy) is True


def test_should_retry_exhausted():
    policy = RetryPolicy(max_attempts=2, interval_seconds=10)
    state = RetryState(attempts=2, last_attempt=datetime.utcnow())
    assert should_retry(state, policy) is False


def test_should_retry_interval_not_elapsed():
    policy = RetryPolicy(max_attempts=5, interval_seconds=120)
    now = datetime.utcnow()
    state = RetryState(attempts=1, last_attempt=now - timedelta(seconds=30))
    assert should_retry(state, policy, now=now) is False


def test_should_retry_interval_elapsed():
    policy = RetryPolicy(max_attempts=5, interval_seconds=60)
    now = datetime.utcnow()
    state = RetryState(attempts=1, last_attempt=now - timedelta(seconds=90))
    assert should_retry(state, policy, now=now) is True


# ---------------------------------------------------------------------------
# record_attempt
# ---------------------------------------------------------------------------

def test_record_attempt_increments_counter():
    state = RetryState(attempts=1)
    now = datetime.utcnow()
    new_state = record_attempt(state, now=now)
    assert new_state.attempts == 2
    assert new_state.last_attempt == now


def test_record_attempt_does_not_mutate_original():
    state = RetryState(attempts=0)
    record_attempt(state)
    assert state.attempts == 0


# ---------------------------------------------------------------------------
# build_retry_registry
# ---------------------------------------------------------------------------

def test_build_retry_registry_empty():
    registry = build_retry_registry()
    assert registry == {}


def test_retry_registry_stores_state():
    registry = build_retry_registry()
    registry["job_a"] = record_attempt(RetryState())
    assert registry["job_a"].attempts == 1
