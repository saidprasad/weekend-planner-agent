"""Unit tests for main CLI (argument parsing, exit codes, output)."""

from __future__ import annotations

from unittest.mock import patch
import sys

import pytest

# Import main after we may have changed argv
import main


def test_main_success_prints_recommendation_and_returns_zero(capsys):
    with patch("main.get_weekend_recommendation", return_value="Go hiking at dawn."):
        with patch.object(sys, "argv", ["main.py", "San Francisco"]):
            exit_code = main.main()
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert "Go hiking at dawn." in out
    assert err == ""


def test_main_success_with_model_flag(capsys):
    with patch("main.get_weekend_recommendation", return_value="Nice day for a walk.") as rec_mock:
        with patch.object(sys, "argv", ["main.py", "London", "--model", "gpt-4o"]):
            exit_code = main.main()
    assert exit_code == 0
    rec_mock.assert_called_once_with("London", model="gpt-4o")


def test_main_value_error_returns_one_and_prints_to_stderr(capsys):
    with patch("main.get_weekend_recommendation", side_effect=ValueError("OPENAI_API_KEY is not set")):
        with patch.object(sys, "argv", ["main.py", "Tokyo"]):
            exit_code = main.main()
    assert exit_code == 1
    out, err = capsys.readouterr()
    assert "OPENAI_API_KEY" in err or "Error" in err
    assert "OPENAI_API_KEY" in err or "Error" in err


def test_main_generic_exception_returns_one(capsys):
    with patch("main.get_weekend_recommendation", side_effect=RuntimeError("Network error")):
        with patch.object(sys, "argv", ["main.py", "Berlin"]):
            exit_code = main.main()
    assert exit_code == 1
    _, err = capsys.readouterr()
    assert "Network error" in err or "Error" in err


def test_main_passes_location_to_agent(capsys):
    with patch("main.get_weekend_recommendation", return_value="Done.") as rec_mock:
        with patch.object(sys, "argv", ["main.py", "90210"]):
            main.main()
    rec_mock.assert_called_once()
    assert rec_mock.call_args[0][0] == "90210"
    assert rec_mock.call_args[1].get("model") is None
