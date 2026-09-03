"""Tests for Day 6 Pydantic models and CLI output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from day06 import AnalysisOutput, RequirementData, parse_requirement
from day06.cli import build_output, run


def test_day5_parser_behavior_is_preserved() -> None:
    result = parse_requirement(
        "機能: 登録\n受入条件： 必須\nリスク: 遅延\n備考: 対象外"
    )
    assert result["functions"] == ["登録"]
    assert result["acceptance_criteria"] == ["必須"]
    assert result["risks"] == ["遅延"]
    assert result["unknown"] == ["備考: 対象外"]


def test_requirement_data_accepts_parser_result_and_adds_defaults() -> None:
    model = RequirementData.model_validate(
        {
            "functions": ["登録"],
            "acceptance_criteria": ["必須"],
        }
    )
    assert model.functions == ["登録"]
    assert model.risks == []
    assert model.questions == []


def test_requirement_data_defaults_are_independent() -> None:
    # TODO 5: 创建两个模型，只修改第一个的 functions，再检查第二个。
    pytest.fail("TODO 5: test independent default lists")


def test_requirement_data_rejects_wrong_field_type() -> None:
    # TODO 6: 使用 pytest.raises(ValidationError) 检查字符串不能替代 list。
    pytest.fail("TODO 6: test Pydantic ValidationError")


def test_requirement_data_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RequirementData.model_validate({"functionz": ["拼错的字段名"]})


def test_analysis_output_has_versioned_dump() -> None:
    output = build_output(
        {
            "functions": ["登録"],
            "acceptance_criteria": ["必須"],
            "risks": [],
            "questions": [],
            "unknown": [],
        },
        [],
    )
    dumped = output.model_dump()
    assert dumped["schema_version"] == "1.0"
    assert dumped["requirements"]["functions"] == ["登録"]
    assert dumped["validation_errors"] == []


def test_run_writes_pydantic_json_for_valid_input(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.json"
    input_path.write_text("機能: 登録\n受入条件: 必須\n", encoding="utf-8")

    assert run(input_path, output_path) == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["requirements"]["functions"] == ["登録"]
    assert payload["validation_errors"] == []


def test_run_still_writes_json_for_business_errors(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.json"
    input_path.write_text("備考: 対象外", encoding="utf-8")

    assert run(input_path, output_path) == 2
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["validation_errors"]) == 2
