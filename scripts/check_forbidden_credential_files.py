from __future__ import annotations

import sys
from pathlib import PurePath

FORBIDDEN_FILENAMES = {".env", ".npmrc", ".pypirc"}
FORBIDDEN_ENV_PREFIX = ".env."
ALLOWED_ENV_EXAMPLES = {".env.example"}


def is_forbidden_credential_file(path: str) -> bool:
    """Return whether the path points to a tracked credential file."""
    filename = PurePath(path).name

    if filename in FORBIDDEN_FILENAMES:
        return True

    if filename in ALLOWED_ENV_EXAMPLES:
        return False

    if filename.startswith(FORBIDDEN_ENV_PREFIX):
        return True

    return False


def main() -> int:
    """Reject tracked credential files before they can be committed."""
    blocked_files = [path for path in sys.argv[1:] if is_forbidden_credential_file(path)]

    if not blocked_files:
        return 0

    print("Refusing to commit credential files:")
    for path in blocked_files:
        print(f"  - {path}")

    print("Use .env.example for templates and keep real credentials outside git.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
