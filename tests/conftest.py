"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def event_loop_policy():
    """Use default asyncio event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
