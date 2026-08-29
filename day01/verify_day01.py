"""Self-check for Day 1. This file does not contain the implementation."""

from __future__ import annotations

from day01_requirement_parser import classify_line, parse_requirement


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    check(classify_line("") is None, "空行を無視できていません")
    check(classify_line("   # comment") is None, "コメント行を無視できていません")
    check(
        classify_line("機能: CSV出力") == ("functions", "CSV出力"),
        "機能行の分類が正しくありません",
    )
    check(
        classify_line("備考: 対象外") == ("unknown", "備考: 対象外"),
        "未知の行をunknownへ入れられていません",
    )

    result = parse_requirement(
        "機能: 登録\n受入条件: 必須\nリスク: 漏えい\n確認事項: 保持期間\n自由記述"
    )
    check(
        set(result)
        == {"functions", "acceptance_criteria", "risks", "questions", "unknown"},
        "結果のキーが仕様と一致しません",
    )
    check(result["functions"] == ["登録"], "functionsの内容が正しくありません")
    check(
        result["acceptance_criteria"] == ["必須"],
        "acceptance_criteriaの内容が正しくありません",
    )
    check(result["risks"] == ["漏えい"], "risksの内容が正しくありません")
    check(result["questions"] == ["保持期間"], "questionsの内容が正しくありません")
    check(result["unknown"] == ["自由記述"], "unknownの内容が正しくありません")

    print("DAY 1 PASS")


if __name__ == "__main__":
    main()
