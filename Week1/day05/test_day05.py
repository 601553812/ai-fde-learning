"""Tests for Day 5 parsing, validation, argparse, and CLI behavior."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from Week1.day05 import (
    RequirementItem,
    classify_line,
    empty_result,
    parse_requirement,
    validate_result,
)
from Week1.day05.cli import build_parser, run


def test_public_package_interface_is_available() -> None:
    item = RequirementItem(category="functions", content="CSV出力")
    assert item.category == "functions"
    with pytest.raises(FrozenInstanceError):
        item.category = "risks"  # type: ignore[misc]


def test_blank_and_comment_lines_are_ignored() -> None:
    assert classify_line("") is None
    assert classify_line("   # comment") is None


def test_ascii_colon_is_supported() -> None:
    assert classify_line("機能: CSV出力") == RequirementItem(
        category="functions",
        content="CSV出力",
    )


def test_full_width_colon_is_supported() -> None:
    assert classify_line("受入条件： 3秒以内") == RequirementItem(
        category="acceptance_criteria",
        content="3秒以内",
    )


def test_unknown_line_is_preserved() -> None:
    assert classify_line("備考: 対象外") == RequirementItem(
        category="unknown",
        content="備考: 対象外",
    )


def test_content_can_contain_another_colon() -> None:
    assert classify_line(
        "確認事項: URLはhttps://example.comでよいか"
    ) == RequirementItem(
        category="questions",
        content="URLはhttps://example.comでよいか",
    )


def test_known_label_without_separator_becomes_unknown() -> None:
    assert classify_line("機能 CSV出力") == RequirementItem(
        category="unknown",
        content="機能 CSV出力",
    )


def test_multiple_lines_are_parsed() -> None:
    result = parse_requirement("機能: 登録\n受入条件： 必須\n自由記述\n# 無視")
    assert result["functions"] == ["登録"]
    assert result["acceptance_criteria"] == ["必須"]
    assert result["unknown"] == ["自由記述"]


def test_validation_reports_missing_functions() -> None:
    result = empty_result()
    result["acceptance_criteria"].append("受入条件あり")
    assert validate_result(result) == ["At least one function is required"]


def test_validation_reports_missing_acceptance_criteria() -> None:
    result = empty_result()
    result["functions"].append("機能あり")
    assert validate_result(result) == [
        "At least one acceptance criterion is required"
    ]


def test_validation_reports_both_required_sections_missing() -> None:
    assert validate_result(empty_result()) == [
        "At least one function is required",
        "At least one acceptance criterion is required",
    ]


def test_known_label_without_content_becomes_unknown() -> None:
    assert classify_line("機能：") == RequirementItem(
        category="unknown",
        content="機能：",
    )


def test_build_parser_converts_paths_and_defaults_verbose() -> None:
    args = build_parser().parse_args(["input.txt", "output.json"])
    assert args.input_path == Path("input.txt")
    assert args.output_path == Path("output.json")
    assert args.verbose is False


def test_build_parser_accepts_verbose_flag() -> None:
    args = build_parser().parse_args(["input.txt", "output.json", "--verbose"])
    assert args.verbose is True


def test_run_writes_valid_json_for_valid_input(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.json"
    input_path.write_text("機能: 登録\n受入条件: 必須\n", encoding="utf-8")

    assert run(input_path, output_path) == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["requirements"]["functions"] == ["登録"]
    assert payload["validation_errors"] == []


def test_run_returns_one_for_missing_input(tmp_path: Path) -> None:
    # TODO 5: 使用 tmp_path 创建不存在的输入路径和输出路径。
    output_path = tmp_path / "output.json"
    assert run(tmp_path / "input.txt", tmp_path / "output.json") == 1
    assert not output_path.exists()



def test_run_returns_two_for_validation_errors(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("12345",encoding="utf-8")
    output_path = tmp_path / "output.json"
    assert run(tmp_path / "input.txt", tmp_path / "output.json") == 2
    assert output_path.exists()
    path = tmp_path / "output.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    validation_errors = payload["validation_errors"]
    error_list = list(validation_errors)
    assert len(error_list) == 2
