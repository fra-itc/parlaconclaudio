"""
Secrets Management Utility

Provides secure secret loading from Docker secrets with fallback to environment variables.
Supports both local development (with .env) and production (with Docker secrets).

Docker secrets are mounted at /run/secrets/ in containers.
This module reads from that location first, then falls back to environment variables.

Author: RTSTT DevOps Team
Date: 2025-11-23
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Docker secrets directory
DOCKER_SECRETS_DIR = Path("/run/secrets")


def get_secret(
    secret_name: str,
    env_var_name: Optional[str] = None,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Get a secret value from Docker secrets or environment variables.

    Priority order:
    1. Docker secret file at /run/secrets/{secret_name}
    2. Environment variable {env_var_name} or {secret_name}
    3. Default value
    4. None (or raises error if required=True)

    Args:
        secret_name: Name of the Docker secret file (e.g., "hf_token")
        env_var_name: Environment variable name (defaults to secret_name.upper())
        default: Default value if secret not found
        required: Raise ValueError if secret not found

    Returns:
        Secret value as string, or None if not found and not required

    Raises:
        ValueError: If required=True and secret not found

    Examples:
        >>> # Read HuggingFace token
        >>> hf_token = get_secret("hf_token", "HF_TOKEN")

        >>> # Read with default
        >>> redis_password = get_secret("redis_password", "REDIS_PASSWORD", default="")

        >>> # Require secret
        >>> jwt_secret = get_secret("jwt_secret", "JWT_SECRET_KEY", required=True)
    """
    # Normalize secret name (no .txt extension)
    if secret_name.endswith('.txt'):
        secret_name = secret_name[:-4]

    # Default env var name is uppercase version of secret_name
    if env_var_name is None:
        env_var_name = secret_name.upper()

    # Try Docker secret file first
    secret_file = DOCKER_SECRETS_DIR / secret_name
    if secret_file.exists() and secret_file.is_file():
        try:
            with open(secret_file, 'r') as f:
                value = f.read().strip()
            if value:  # Only use if non-empty
                logger.debug(f"Loaded secret '{secret_name}' from Docker secrets")
                return value
            else:
                logger.debug(f"Docker secret '{secret_name}' is empty, trying environment variable")
        except Exception as e:
            logger.warning(f"Error reading Docker secret '{secret_name}': {e}")

    # Also check for _FILE environment variable (docker-compose pattern)
    env_file_var = f"{env_var_name}_FILE"
    env_file_path = os.getenv(env_file_var)
    if env_file_path:
        try:
            with open(env_file_path, 'r') as f:
                value = f.read().strip()
            if value:
                logger.debug(f"Loaded secret '{secret_name}' from {env_file_var}={env_file_path}")
                return value
        except Exception as e:
            logger.warning(f"Error reading secret from {env_file_path}: {e}")

    # Try environment variable
    value = os.getenv(env_var_name)
    if value is not None:
        logger.debug(f"Loaded secret '{secret_name}' from environment variable {env_var_name}")
        return value

    # Use default if provided
    if default is not None:
        logger.debug(f"Using default value for secret '{secret_name}'")
        return default

    # Handle required secrets
    if required:
        error_msg = (
            f"Required secret '{secret_name}' not found. "
            f"Checked: Docker secret (/run/secrets/{secret_name}), "
            f"environment variable ({env_var_name}), "
            f"and {env_file_var}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug(f"Secret '{secret_name}' not found, returning None")
    return None


def get_hf_token(required: bool = False) -> Optional[str]:
    """
    Get HuggingFace token.

    Args:
        required: Raise error if not found

    Returns:
        HuggingFace token or None
    """
    return get_secret("hf_token", "HF_TOKEN", required=required)


def get_redis_password(default: str = "") -> str:
    """
    Get Redis password.

    Args:
        default: Default value (empty string for no auth)

    Returns:
        Redis password
    """
    return get_secret("redis_password", "REDIS_PASSWORD", default=default) or default


def get_jwt_secret(required: bool = False) -> Optional[str]:
    """
    Get JWT signing secret.

    Args:
        required: Raise error if not found

    Returns:
        JWT secret or None
    """
    return get_secret("jwt_secret", "JWT_SECRET_KEY", required=required)


def get_grafana_admin_password(default: str = "admin") -> str:
    """
    Get Grafana admin password.

    Args:
        default: Default value

    Returns:
        Grafana admin password
    """
    return get_secret("grafana_admin_password", "GRAFANA_ADMIN_PASSWORD", default=default) or default


def check_secrets_available() -> dict:
    """
    Check which secrets are available.

    Returns:
        Dictionary with secret availability status
    """
    secrets = {
        "hf_token": get_hf_token() is not None,
        "redis_password": get_redis_password() != "",
        "jwt_secret": get_jwt_secret() is not None,
        "grafana_admin_password": get_grafana_admin_password() != "admin",
    }

    # Check Docker secrets directory
    secrets["docker_secrets_dir_exists"] = DOCKER_SECRETS_DIR.exists()

    return secrets


def log_secrets_status():
    """Log the status of available secrets (for debugging)."""
    status = check_secrets_available()

    logger.info("Secrets availability:")
    logger.info(f"  Docker secrets dir: {'✓' if status['docker_secrets_dir_exists'] else '✗'}")
    logger.info(f"  HF_TOKEN: {'✓' if status['hf_token'] else '✗'}")
    logger.info(f"  REDIS_PASSWORD: {'✓' if status['redis_password'] else '✗ (using empty)'}")
    logger.info(f"  JWT_SECRET_KEY: {'✓' if status['jwt_secret'] else '✗ (not set)'}")
    logger.info(f"  GRAFANA_ADMIN_PASSWORD: {'✓' if status['grafana_admin_password'] else '✗ (using default)'}")


if __name__ == "__main__":
    # Test the secrets module
    logging.basicConfig(level=logging.DEBUG)

    print("Testing secrets module...")
    print()

    status = check_secrets_available()
    print("Secrets availability:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    print()
    log_secrets_status()
