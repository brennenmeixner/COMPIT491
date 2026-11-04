"""Assert the hardening of the Compose test container, which shares its settings with app."""

import os
import socket
from pathlib import Path

import pytest

pytestmark = pytest.mark.container

# A documentation address (RFC 5737). Nothing should answer, and no packet should leave.
OUTSIDE_ADDRESS = ("192.0.2.1", 80)


def test_container_runs_as_non_root() -> None:
    assert os.getuid() != 0


def test_root_filesystem_is_mounted_read_only() -> None:
    mounts = (line.split() for line in Path("/proc/self/mounts").read_text().splitlines())
    root_options = next(fields[3] for fields in mounts if fields[1] == "/")
    assert "ro" in root_options.split(",")


def test_outside_network_has_no_route() -> None:
    # The error must be "no route", not a timeout: a timeout would also occur on a
    # network with a route out, so it would not prove the isolation.
    with pytest.raises(OSError, match="unreachable"):
        socket.create_connection(OUTSIDE_ADDRESS, timeout=3)
