"""Pytest exercises for Day 3."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from day03_requirement_parser import (
    RequirementItem,
    classify_line,
    parse_requirement,
    validate_result,
)


def test_requirement_item_has_named_fields_and_is_frozen() -> None:
    item = RequirementItem(category="functions", content="CSV出力")
    assert item.category == "functions"
    assert item.content == "CSV出力"
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


def test_multiple_lines_are_parsed() -> None:
    result = parse_requirement("機能: 登録\n受入条件： 必須\n自由記述\n# 無視")
    assert result["functions"] == ["登録"]
    assert result["acceptance_criteria"] == ["必須"]
    assert result["unknown"] == ["自由記述"]


def test_content_can_contain_another_colon() -> None:
    # TODO 4: 验证输入「確認事項: URLはhttps://example.comでよいか」不会截断。
    pytest.fail("TODO 4: write this test")


def test_known_label_without_content_becomes_unknown() -> None:
    # TODO 5: 验证输入「機能：」会作为 unknown 原样保留。
    pytest.fail("TODO 5: write this test")


def test_validation_reports_missing_functions() -> None:
    # TODO 6: empty_result 中只有 acceptance_criteria 时，应报告缺少 functions。
    pytest.fail("TODO 6: write this test")


def test_validation_reports_missing_acceptance_criteria() -> None:
    # TODO 7: empty_result 中只有 functions 时，应报告缺少 acceptance_criteria。
    pytest.fail("TODO 7: write this test")
