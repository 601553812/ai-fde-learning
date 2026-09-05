# Day 8 — 看懂并编写 HTTP CLI 单元测试

日期：2026-09-05（日本时间）

计划用时：90～120 分钟

唯一主主题：通过一个 HTTP CLI 集成边界，掌握 pytest 的调用链、测试替身、`monkeypatch` 和 Arrange–Act–Assert。

## 为什么今天先不进入 FastAPI

Day 7 已能调用 JSON HTTP API，但复盘中记录的当前弱项是：Python 调用链阅读较慢，对被测对象、外部依赖、测试替身和 Arrange–Act–Assert 还不熟练。今天先把这条链真正看懂并独立写出测试：

```text
test_day08
  → day08.cli.run(argv)
      → day08.cli.fetch_requirement(url, timeout_seconds)
          → requests.get(url, timeout)
              → Response.raise_for_status()
              → Response.json()
          → RequirementData.model_validate(payload)
      → output.write_text(..., encoding="utf-8")
```

Day 8 完成后，Day 9 再进入 FastAPI 会更稳，因为届时你已经知道如何把外部 HTTP 调用隔离在测试之外。

## 今天的产出

实现以下命令：

```powershell
.\.venv\Scripts\python.exe -m day08.cli <URL> <OUTPUT> --timeout 2.5
```

成功时：

- 调用 Day 7 的 `fetch_requirement()`。
- 把验证后的模型写成 UTF-8 JSON。
- 返回退出码 `0`。

失败时：

- 捕获 `RequirementApiError`。
- 记录一条 ERROR 日志。
- 返回退出码 `1`。
- 不创建输出文件。

## 今天只学这 6 个知识点

### 1. 被测对象与外部依赖

测试 `day08.cli.run()` 时，被测对象是 `run()`；它的外部依赖是 `fetch_requirement()`。这里不需要再深入模拟 `requests.get()`，否则一个 CLI 测试会同时验证太多层。

类比 Java：这和测试 Service 时替换 Repository/HTTP Client 的思路相近。区别是今天不引入接口或 mock 框架，而是临时替换 Python 名称所指向的函数。

### 2. `monkeypatch` 替换的是“代码实际查找的名称”

`cli.py` 使用了：

```python
from Week1.day07.api_client import fetch_requirement
```

所以 `run()` 执行时查找的是 `day08.cli.fetch_requirement`。CLI 测试应替换这个名称：

```python
monkeypatch.setattr("day08.cli.fetch_requirement", fake_fetch)
```

测试结束后 pytest 会自动恢复原值。

### 3. Fake 的职责要小

- `fake_get()`：替代 `requests.get()`，用于测试 Day 7 HTTP 客户端。
- `FakeResponse`：替代 Requests 的 `Response` 对象，只实现当天会调用的方法。
- `fake_fetch()`：替代完整的 `fetch_requirement()`，用于测试 Day 8 CLI。

Fake 不需要复制真实库的全部行为，只需要提供被测代码会访问的最小接口。

### 4. Arrange–Act–Assert

```text
Arrange：准备输入、Fake、临时路径，并安装 monkeypatch
Act：只调用一次被测函数
Assert：检查返回值、传参、文件内容或异常原因
```

如果一段测试看不懂，先给这三段加注释，再逐行判断每行属于哪一段。

### 5. 默认参数与非默认参数测试保护不同风险

- 省略 timeout，断言传入底层的是 `5.0`：保护默认行为。
- 显式传入 `2.5`，断言底层收到 `2.5`：防止生产代码把 timeout 写死。

只测默认值时，即使实现永远写死 `5.0`，测试也可能错误地通过。

### 6. JSON 解析错误与 Schema 错误

```text
response.json() 失败
  → requests.JSONDecodeError

response.json() 成功，但字段结构不符合 RequirementData
  → pydantic.ValidationError
```

对外两者都变成 `RequirementApiError`，但 `raise ... from exc` 让 `__cause__` 保留不同原始原因。测试既要验证统一边界，也要验证调查线索没有丢失。

## Java / Kotlin 对照速查

| Python / pytest | Java / Kotlin 中可先类比为 | 类比边界 |
|---|---|---|
| `monkeypatch.setattr(...)` | 临时注入 Stub/Mock | Python 替换运行时名称，不要求先定义 interface |
| `FakeResponse` | 手写 Fake HTTP Response | 只实现测试需要的少量方法，不是完整实现 |
| `tmp_path` | 测试专用临时目录 | pytest 自动为每个测试提供独立 `Path` |
| `with pytest.raises(...)` | `assertThrows(...)` | `as caught` 可继续检查异常对象和 `__cause__` |
| `argv: Sequence[str] | None` | 可传入的命令行参数列表 | 类型标注本身不执行运行时校验 |

## 今天不需要学习

- `unittest.mock`、`MagicMock`、pytest fixture 自定义与 scope。
- 测试覆盖率工具、参数化测试、集成测试服务器。
- FastAPI、异步 HTTP、重试、认证、Session。
- 依赖注入框架或复杂测试架构。

官方资料只作扩展查阅，不需要通读：

- [pytest monkeypatch 官方说明](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [pytest tmp_path 官方说明](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

## 需要完成的 7 个 TODO

### TODO 1：实现 CLI 正常路径

修改文件：`day08/cli.py`

输入：`run(argv)` 接收 URL、输出路径和可选的 `--timeout`。

处理步骤：

脚手架已经用 `build_parser().parse_args(argv)` 完成参数解析。你需要继续：

1. 调用 `fetch_requirement(args.url, timeout_seconds=args.timeout)`。
2. 使用模型的 `model_dump_json(indent=2)` 得到 JSON 字符串。
3. 使用 `args.output.write_text(..., encoding="utf-8")` 写入文件。
4. 记录 INFO 日志并返回 `0`。

输出：UTF-8 JSON 文件，顶层字段来自 Day 6 的 `RequirementData`。

完成条件：CLI 测试能确认 URL、非默认 timeout、退出码、文件编码和 JSON 内容。

### TODO 2：实现 CLI 错误路径

修改文件：`day08/cli.py`

异常：只捕获 `RequirementApiError`，记录 `LOGGER.error(...)` 并返回 `1`。不要捕获宽泛的 `Exception`。

输出约束：调用失败时不得创建输出文件。

完成条件：错误路径测试同时断言退出码为 `1` 且输出文件不存在。

### TODO 3：测试默认 timeout

修改文件：`day08/test_day08.py`

1. Arrange：定义 `fake_get(url, timeout)`，记录收到的 timeout，并返回合法 `FakeResponse`。
2. Arrange：替换 `Week1.day07.api_client.requests.get`。
3. Act：调用 `fetch_requirement(url)`，不要显式传 timeout。
4. Assert：收到的 timeout 是 `5.0`，返回值是 `RequirementData`。

### TODO 4：测试非法 JSON 的原始原因

修改文件：`day08/test_day08.py`

让 `FakeResponse.json()` 抛出 `requests.JSONDecodeError`。使用 `pytest.raises(RequirementApiError) as caught` 捕获公开异常，并断言 `caught.value.__cause__` 是该 JSON 异常对象。

### TODO 5：测试 Schema 错误的原始原因

修改文件：`day08/test_day08.py`

让 `FakeResponse` 返回合法 Python dict，但 `functions` 的值故意使用字符串而不是 list。捕获 `RequirementApiError`，断言它的 `__cause__` 是 `ValidationError`。

### TODO 6：测试 CLI 正常路径

修改文件：`day08/test_day08.py`

1. Arrange：用 `RequirementData.model_validate(VALID_PAYLOAD)` 准备返回模型。
2. Arrange：定义 `fake_fetch(url, timeout_seconds)`，在函数内断言 URL 与 `2.5`。
3. Arrange：替换 `day08.cli.fetch_requirement`，用 `tmp_path / "output.json"` 作为输出路径。
4. Act：调用 `run([url, str(output_path), "--timeout", "2.5"])`。
5. Assert：退出码为 `0`、文件存在、UTF-8 JSON 能读回，且功能列表正确。

### TODO 7：测试 CLI 错误路径

修改文件：`day08/test_day08.py`

让 `fake_fetch()` 抛出 `RequirementApiError`。调用 `run()` 后断言退出码为 `1`，并明确断言 `not output_path.exists()`。

## 时间安排

- 0～15 分钟：填写学习开始记录，阅读调用链和 6 个最小知识点。
- 15～35 分钟：把 Day 7 的一个现有测试手动标出 Arrange / Act / Assert。
- 35～60 分钟：完成 TODO 3～5，理解 HTTP 客户端这一层。
- 60～85 分钟：完成 TODO 1～2，实现 CLI 边界。
- 85～110 分钟：完成 TODO 6～7，理解为什么 CLI 测试不碰真实网络。
- 110～120 分钟：运行验收并填写复盘。

## 运行与预期结果

在仓库根目录使用 PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pytest .\Week1\day06\test_day06.py .\Week1\day07\test_day07.py .\day08\test_day08.py -q
```

初始脚手架预期：`15 passed, 5 failed`。这 5 个失败都是 `test_day08.py` 中明确标注的待完成练习，不是项目故障。

完成全部 TODO 后预期：`20 passed`。

手动验证帮助：

```powershell
.\.venv\Scripts\python.exe -m day08.cli --help
```

完成后可复用 Day 7 的本机 HTTP 服务器做一次真实调用：

终端 A：

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory .\Week1\day07
```

终端 B：

```powershell
.\.venv\Scripts\python.exe -m day08.cli http://127.0.0.1:8000/sample_requirement.json .\day08\output.json --timeout 2.5
```

测试结束后删除手动生成的 `day08/output.json`，不要提交生成结果。

## 完成标准

- Day 6～8 合计 `20 passed`，并确认 Day 8 五个测试包含真实断言，不是只删除 `pytest.fail()`。
- 能画出并说明 `test → run → fetch_requirement → requests.get` 调用链。
- 默认 timeout 与非默认 timeout 都有测试保护。
- 非法 JSON 与 Schema 错误都统一为 `RequirementApiError`，且原始原因类型仍可区分。
- CLI 成功时生成可读的 UTF-8 JSON 并返回 `0`。
- CLI 失败时返回 `1`、无 traceback、没有输出文件。
- `python -m day08.cli --help` 返回 `0`。
- 完成 `day08_notes.md` 的学习后复盘。

完成后告诉我：

```text
Day 8 完成，请检查
```
