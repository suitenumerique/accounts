"""Convenience runner for the local OIDC mock IdP."""

try:
    from .server import main
except ImportError:  # pragma: no cover
    from server import main


if __name__ == "__main__":
    main()


