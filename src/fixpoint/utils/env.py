"""Utility functions for the environment"""

import os


def get_env_value(key: str) -> str:
    """Get the value of an environment variable"""
    value = os.environ.get(key)
    if value is None:
        raise EnvironmentError(
            f"Invalid {key}. Ensure that it is set in the environment."
        )
    return value
