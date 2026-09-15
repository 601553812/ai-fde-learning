"""Read-only observation demo: python -m Week2.day12.review_flow."""

import pytest
from fastapi.testclient import TestClient

from Week2.day11.app import app
from Week2.day11.service import RuleBasedAnalyzer, get_analyzer
from Week2.day12.exercise import FixedAnalyzer, make_fixed_output


def main() -> None:
    text = "機能: CSV出力\n受入条件: 3秒以内"
    expected = make_fixed_output()
    fake = FixedAnalyzer(expected)
    provider_calls: list[str] = []
    original = dict(app.dependency_overrides)
    client = TestClient(app)
    monkeypatch = pytest.MonkeyPatch()

    def get_test_analyzer():
        provider_calls.append("get_test_analyzer")
        print("  get_test_analyzer 被调用：返回已有的 fake 对象")
        return fake

    with monkeypatch.context() as patch:
        patch.setitem(app.dependency_overrides, get_analyzer, get_test_analyzer)

        print("1. 已安装替换规则，但直接调用普通函数 get_analyzer()")
        direct = get_analyzer()
        print("  得到的类型：", type(direct).__name__)
        assert type(direct) is RuleBasedAnalyzer
        assert provider_calls == []
        assert fake.calls == []

        print("2. 通过 TestClient 发正常请求，让 FastAPI 处理 Depends")
        response = client.post("/analyze-requirement", json={"text": text})
        print("  状态码：", response.status_code)
        print("  功能列表：", response.json()["requirements"]["functions"])
        assert response.status_code == 200
        assert response.json() == expected.model_dump()
        assert provider_calls == ["get_test_analyzer"]
        assert fake.calls == [text]

        print("3. 再发 2001 字符请求，观察取得对象与执行分析的区别")
        rejected = client.post("/analyze-requirement", json={"text": "あ" * 2001})
        print("  状态码：", rejected.status_code)
        print("  提供对象的函数累计执行次数：", len(provider_calls))
        print("  fake.analyze 累计执行次数：", len(fake.calls))
        assert rejected.status_code == 413
        assert rejected.json() == {
            "detail": {"code": "TEXT_TOO_LONG", "max_length": 2000, "actual_length": 2001}
        }
        assert provider_calls == ["get_test_analyzer", "get_test_analyzer"]
        assert fake.calls == [text]

    print("4. 离开 with，再发正常请求")
    assert app.dependency_overrides == original
    restored = client.post("/analyze-requirement", json={"text": text})
    print("  状态码：", restored.status_code)
    print("  功能列表：", restored.json()["requirements"]["functions"])
    assert restored.status_code == 200
    assert restored.json()["requirements"]["functions"] == ["CSV出力"]
    assert provider_calls == ["get_test_analyzer", "get_test_analyzer"]
    assert fake.calls == [text]
    print("观察验证通过；临时替换已经恢复。")


if __name__ == "__main__":
    main()
