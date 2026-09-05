"""Automatic checks for Day 2. Do not place the implementation in this file."""

from __future__ import annotations

import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from day02_requirement_parser import classify_line, parse_requirement, run


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    check(classify_line("") is None, "空行を無視できていません")
    check(classify_line("   # comment") is None, "コメント行を無視できていません")
    check(
        classify_line("機能: CSV出力") == ("functions", "CSV出力"),
        "半角コロンの機能行を分類できていません",
    )
    check(
        classify_line("受入条件： 3秒以内")
        == ("acceptance_criteria", "3秒以内"),
        "全角コロンの受入条件を分類できていません",
    )
    check(
        classify_line("備考: 対象外") == ("unknown", "備考: 対象外"),
        "未知の行をunknownへ入れられていません",
    )
    check(
        classify_line("機能：") == ("unknown", "機能："),
        "内容が空の既知ラベルをunknownへ入れられていません",
    )

    result = parse_requirement(
        "機能: 登録\n受入条件： 必須\nリスク: 漏えい\n"
        "確認事項： 保持期間\n自由記述\n# 無視"
    )
    check(
        result
        == {
            "functions": ["登録"],
            "acceptance_criteria": ["必須"],
            "risks": ["漏えい"],
            "questions": ["保持期間"],
            "unknown": ["自由記述"],
        },
        "複数行の解析結果が仕様と一致しません",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        missing_input = base / "missing.txt"
        output_path = base / "result.json"
        captured = StringIO()
        with redirect_stdout(captured):
            exit_code = run(missing_input, output_path)
        check(exit_code == 1, "入力ファイルがない場合の終了コードは1です")
        check(
            "Input file not found:" in captured.getvalue(),
            "入力ファイルがない場合の短いエラーメッセージがありません",
        )
        check(not output_path.exists(), "失敗時にJSONを作成しないでください")

        input_path = base / "input.txt"
        input_path.write_text("機能： 検索\n", encoding="utf-8")
        captured = StringIO()
        with redirect_stdout(captured):
            exit_code = run(input_path, output_path)
        check(exit_code == 0, "正常終了時の終了コードは0です")
        check(output_path.exists(), "正常終了時にJSONが作成されていません")
        written = json.loads(output_path.read_text(encoding="utf-8"))
        check(written["functions"] == ["検索"], "出力JSONの内容が正しくありません")
        check("Created:" in captured.getvalue(), "正常終了メッセージがありません")

    print("DAY 2 PASS")


if __name__ == "__main__":
    main()
