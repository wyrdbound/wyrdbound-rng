"""
Tests for the command-line interface.
"""

import pytest

from wyrdbound_rng import __version__
from wyrdbound_rng.cli import main


def test_version_reports_the_package_version(monkeypatch, capsys):
    """`--version` prints the installed package's version, not a fixed one."""
    monkeypatch.setattr("sys.argv", ["wyrdbound-rng", "--version"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"wyrdbound-rng {__version__}"
