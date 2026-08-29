import os
import sys
from collections.abc import Iterator

import pytest

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

LOCKFILE_PATH = os.path.join(os.path.dirname(__file__), ".pytest_lock")


@pytest.fixture
def lock_test() -> Iterator[None]:
    """Cross-platform, process-safe lock fixture for serializing tests."""
    with open(LOCKFILE_PATH, "w") as lockfile:
        if sys.platform == "win32":
            msvcrt.locking(lockfile.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(lockfile, fcntl.LOCK_EX)

        try:
            yield
        finally:
            if sys.platform == "win32":
                msvcrt.locking(lockfile.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lockfile, fcntl.LOCK_UN)

    # 🔥 Clean up lock file after use
    try:
        os.remove(LOCKFILE_PATH)
    except FileNotFoundError:
        pass
    except PermissionError:
        # Windows may still have a file handle open briefly — not a big deal
        pass
