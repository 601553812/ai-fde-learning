"""Provided CLI safeguards; never makes a live request."""

import subprocess
from Week3.day19 import run_call


def test_total_deadline_returns_safe_failure(monkeypatch, capsys):
    def timed_out(*args, **kwargs):
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired(args[0], 30, output="private mock output")
    monkeypatch.setattr(run_call.subprocess, "run", timed_out)
    assert run_call.run_live() == 1
    captured = capsys.readouterr()
    assert '"error": "overall_timeout"' in captured.out
    assert "private mock output" not in captured.out + captured.err
    assert "30" in captured.err
