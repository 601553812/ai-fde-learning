# Day 9 — 用 FastAPI 提供第一个需求分析 API

日期：2026-09-06（日本时间）

状态：已完成（2026-09-07 验收）。计划用时：90～120 分钟；学习者自报实际用时约 1 小时。

验收：Day 9 `10 passed`，Day 6～9 回归 `30 passed`；真实 HTTP 的正常、业务缺项、请求错误、日文 UTF-8 和无输出文件检查通过。下方 TODO 与初始失败说明保留为原始练习要求；复盘订正和学习过程见 `day09_notes.md`。

唯一主主题：把已经验证的需求解析能力通过 HTTP 提供给调用者。

## 今天的成果与范围

Day 7～8 是 HTTP 的调用方；今天开始实现接收请求的服务端。复用 Day 6 的 parser、业务校验和输出模型，只增加 HTTP 入口。这个接口将来可以作为主作品 `/analyze-requirement` 的基础，但今天仍然是普通规则解析，不调用 LLM，也不承诺语义理解。

| 接口/输入 | HTTP 状态码 | 响应 |
|---|---|---|
| `GET /health`，无请求 body | 200 | `{"status": "ok"}` |
| `POST /analyze-requirement`，正确的 text 字符串 | 200 | `AnalysisOutput`，包括提取结果和业务校验列表 |
| text 内容缺少功能或验收条件 | 200 | 同一输出结构，`validation_errors` 列出缺项 |
| JSON 损坏、缺少 text、text 非字符串/空字符串、未知字段 | 422 | FastAPI 的 `{"detail": [...]}` 错误响应 |

这里的 200 表示“分析操作成功完成”，不保证需求内容完整。422 表示请求数据不符合接口契约。这是本练习的设计选择；HTTP 状态码也不是前几天 CLI 的进程退出码。

只包含空格的字符串长度仍大于 0，今天允许它进入 parser 并产生业务缺项。暂不增加去空格验证器。接口不读写结果文件、不调用外部 HTTP API。

## 先看懂这条链

```text
调用者发送 JSON body: {"text": "機能: 登録\n受入条件: 必須"}
  → FastAPI 解析 JSON、使用 Pydantic 校验 AnalyzeRequest
  → 路由函数收到模型实例，使用 request.text
  → parse_requirement(text)：已有的规则解析
  → validate_result(requirements)：已有的业务校验
  → build_output(requirements, errors)：已有的输出模型构造
  → 返回 AnalysisOutput，由 FastAPI 转为 HTTP JSON 响应
```

复习 Day 8：JSON 字符串、Python dict、Pydantic 模型是不同层次。FastAPI 帮你完成请求入口的转换；不需要再自己把模型当字符串解析一次。

## 最小知识集

### 1. FastAPI 和 Uvicorn 分别做什么

- `FastAPI()` 创建应用对象，负责路由、请求校验和响应处理。
- Uvicorn 启动本地 HTTP 服务，把接收到的请求交给应用。
- HTTP 方法和路径共同决定执行哪个函数。例如 GET `/health` 与 POST `/analyze-requirement` 是两个不同入口。

服务持续运行等待多个请求，不像 CLI 处理一次后立即退出。

### 2. 路由装饰器：今天只认识用法

```python
@app.post("/echo")
def echo(body: EchoInput):
    return {"received": body.message}
```

`@app.post("/echo")` 把下面的函数登记为 POST `/echo` 的处理函数。函数名叫 `echo` 不会自动决定 URL，URL 来自装饰器中的字符串。可以先类比 Java Web 框架里的 `@PostMapping`；Python 装饰器是可执行的函数登记机制，并不等同于 Java 注解。今天不用自己编写装饰器或学习其内部实现。

使用普通 `def` 即可，不引入 `async/await`。

### 3. 请求模型：声明参数，框架帮你校验

脚手架已经提供：

```python
class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
```

这里 `Field(min_length=1)` 设置最小长度，没有提供默认值，因此 text 必填。`extra="forbid"` 沿用 Day 6 的未知字段规则。

路由参数写 `request: AnalyzeRequest` 后，FastAPI 知道要从 JSON body 构造该模型。`request` 是参数名，可以换名；它在本题中是模型实例，不是 Requests 的 Response 或 FastAPI 的底层 Request 对象。

Java 类比是“请求 body 绑定到 DTO 并校验”；你不需要先学习 Spring。普通 Python 类型标注本身不强制检查，而 FastAPI 会主动读取标注并配合 Pydantic 执行校验。

### 4. 输出模型：直接返回对象

脚手架已声明 `response_model=AnalysisOutput`。它定义 HTTP 响应契约，FastAPI 负责响应校验和 JSON 序列化。你只需返回已有的模型实例。

不要先返回 `model_dump_json()` 的字符串：那是 Day 8 写文件时需要的形式；今天会与声明的模型响应不符。`response.json()` 则是测试调用者读取响应后，把 JSON body 解析为 Python 数据。

### 5. TestClient：直接给本地应用发送测试请求

最小完整示例（与本题的需求解析不同，仅演示使用方式）：

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

class EchoInput(BaseModel):
    message: str

demo = FastAPI()

@demo.post("/echo")
def echo(body: EchoInput) -> dict[str, str]:
    return {"received": body.message}

client = TestClient(demo)
response = client.post("/echo", json={"message": "こんにちは"})
assert response.status_code == 200
assert response.json() == {"received": "こんにちは"}
```

这里 `json=` 接收 dict，由客户端序列化成请求 JSON；`response.json()` 则把响应 JSON 解析成 dict。方法调用看起来像 Requests，但 TestClient 使用 HTTPX，在进程内调用应用，不需要启动 Uvicorn 或连接互联网。

本题测试走真实路由和纯函数 parser，没有外部依赖，所以无需额外写 Fake 或 monkeypatch。集成多个本地组件是可以的，测试层次由你想验证的行为决定。

### 6. 如何读 422

例如 `client.post(..., json={"text": 123})`：JSON 语法正确，但 text 不是字符串，会被请求模型拒绝。

错误 body 中 `detail` 是错误列表。测试只检查这些稳定信息：

```python
assert response.status_code == 422
assert response.json()["detail"][0]["loc"] == ["body", "text"]
```

`loc` 表示出错位置，`type` 表示错误分类，不需要背诵整条英文消息。非法 JSON 对应 `json_invalid`，错误字段类型对应 `string_type`。此时路由函数还没有执行，所以请求错误测试可以在 TODO 未实现时先通过。

## 今天不需要学习

异步、依赖注入、HTTPException 自定义处理、认证、数据库、外部 LLM 调用、Docker、部署、前端框架、编写装饰器、框架源码、更多 HTTP 方法。本日不把错误处理扩展成第二个主题。

官方资料已筛选，按需查阅即可：[路由入门](https://fastapi.tiangolo.com/tutorial/first-steps/)、[请求 body](https://fastapi.tiangolo.com/tutorial/body/)、[响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)、[TestClient](https://fastapi.tiangolo.com/tutorial/testing/)。不要求通读。

## 环境和文件

根目录 `.venv` 已安装并验证依赖，新增条目记入 `requirements-dev.txt`：FastAPI（应用）、Uvicorn（服务运行）、HTTPX（TestClient 所需）。从全新环境复现时，在仓库根目录运行以下命令，PowerShell 与 CMD/Cmder 通用：

```text
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -c "import fastapi, uvicorn, httpx; print(fastapi.__version__, uvicorn.__version__, httpx.__version__)"
```

需要修改的文件只有 `day09/app.py` 和 `day09/test_day09.py`。`models.py`、路由登记和大部分测试已经提供。Day 9 继续放在根目录，使用 `Week1.day06` 导入归档的已有代码。

## 四个 TODO

### TODO 1：健康检查（app.py）

输入：GET `/health`，没有 body。实现 `health()`，输出 dict `{"status": "ok"}`；FastAPI 默认返回 200。没有业务异常，完成条件是 `test_health_returns_ok` 通过。

### TODO 2：接通已有解析器（app.py）

输入：FastAPI 已校验的 `AnalyzeRequest` 实例。

按顺序完成 `analyze_requirement()`：

1. 从 `request.text` 取原始需求字符串。
2. 调用 `parse_requirement(text)`，得到 `dict[str, list[str]]`。
3. 把上述 dict 传给 `validate_result(requirements)`，取得 `list[str]` 错误列表。
4. 把这两个结果传给 `build_output(requirements, validation_errors)`，返回得到的 `AnalysisOutput` 实例。

这三个函数已经 import 好，不需要重写它们。`build_output()` 位于旧 CLI 模块但本身是纯模型构造函数；只调用它，不调用旧 `run()` 或 `main()`。

正常和业务缺项都返回 HTTP 200；不要为业务缺项抛异常。输入 Schema/JSON 错误交给 FastAPI 自动返回 422。不要宽泛捕获 Exception。完成条件是已提供的正常、业务缺项测试通过，并通过下面两项自己的测试。健康检查和分析接口都不能创建输出文件或进行外部网络访问。

### TODO 3：不同输入测试（test_day09.py）

补完 `test_analyze_uses_another_input()`，删除该函数里的 `pytest.fail()`。

- Arrange：准备 `"機能： CSV出力\n受入条件: 3秒以内"`。
- Act：使用 `client.post(ENDPOINT, json={"text": ...})` 发起请求。
- Assert：状态码 200；功能为 `["CSV出力"]`，验收条件为 `["3秒以内"]`，`validation_errors` 为 `[]`，版本为 `"1.0"`。
- 验证目的：防止接口写死第一份样例响应，并保留全角冒号支持。无需构造异常。

### TODO 4：保留原有分类规则（test_day09.py）

补完 `test_analyze_preserves_questions_and_unknown_lines()`，删除该函数里的 `pytest.fail()`。

- 输入：`"機能: 登録\n受入条件: 必須\n確認事項: 期限はいつか\n備考: 対象外\n# コメント\n"`。
- 使用 TestClient POST，并断言 200。
- 检查 `requirements` 中 functions、acceptance_criteria、questions、unknown 分别为 `["登録"]`、`["必須"]`、`["期限はいつか"]`、`["備考: 対象外"]`；risks 为 `[]`，业务错误为 `[]`。
- 验证目的：未知行必须保留，注释和空行必须忽略；可以通过断言整个 requirements dict 完成，不必学习新测试框架。

## 学习顺序与自动检查

- 0～10 分钟：填写开始时间；复习 JSON 字符串、dict、模型的区别。
- 10～35 分钟：读最小知识集，按输入到输出顺序读 `app.py`。
- 35～60 分钟：完成 TODO 1、2。
- 60～85 分钟：完成 TODO 3、4 并运行测试。
- 85～105 分钟：真实启动服务，通过 `/docs` 和下面的命令验证。
- 105～120 分钟：填写复盘。实际用时自己记录，中断不计入。

以下命令均从根目录执行，PowerShell 与 CMD/Cmder 通用：

```text
.\.venv\Scripts\python.exe -m pytest day09/test_day09.py -q --tb=short
.\.venv\Scripts\python.exe -m pytest Week1/day06/test_day06.py Week1/day07/test_day07.py day08/test_day08.py day09/test_day09.py -q --tb=short
```

初始 Day 9 是 `5 passed, 5 failed`：五项请求错误测试通过；三个接口测试遇到 NotImplementedError，两个测试 TODO 主动失败。合并回归初始为 `25 passed, 5 failed`。完成后应为 Day 9 `10 passed`，合计 `30 passed`。

脚手架已在 Python 3.11.15、FastAPI 0.141.1、Uvicorn 0.52.4、HTTPX 0.28.1 上验证上述初始结果，`pip check` 通过。当前间接依赖会显示两条弃用警告（Starlette/HTTPX 和 AnyIO），不影响今天的测试；它们不是 TODO 错误，今天无需处理或屏蔽。测试失败先找底部的 `day09/app.py` 或 `day09/test_day09.py`，不需要逐层阅读框架调用栈。

TestClient 默认把服务端未捕获的异常重新抛到测试中，便于定位 TODO；因此看到 NotImplementedError 是预期的练习失败。不要用 skip、xfail 或删除断言掩盖它。

## 本地真实 HTTP 验证

终端 A（PowerShell / CMD / Cmder 通用）：

```text
.\.venv\Scripts\python.exe -m uvicorn day09.app:app --host 127.0.0.1 --port 8000 --reload
```

`day09.app:app` 中，冒号前是模块名（`day09/app.py`），冒号后是该模块的应用对象名。`--reload` 在保存代码后重新加载，仅用于本地开发。端口占用时改为 8001，并同步修改下面 URL。

浏览器打开 `http://127.0.0.1:8000/docs`。展开 POST `/analyze-requirement` → Try it out → 粘贴 `sample_request.json` 内容 → Execute，检查状态码和响应 body。地址栏直接访问路径发送的是 GET，不能代替 POST；直接访问 POST 路径得到 405 是方法不匹配。

终端 B（两种 shell 都用 `curl.exe`，避免 PowerShell 的 curl 别名）：

```text
curl.exe -i http://127.0.0.1:8000/health
curl.exe -i -H "Content-Type: application/json" --data-binary "@day09/sample_request.json" http://127.0.0.1:8000/analyze-requirement
curl.exe -i -H "Content-Type: application/json" --data-binary "@day09/invalid_request.json" http://127.0.0.1:8000/analyze-requirement
```

依次预期：200/ok、200/结构化分析、422/text 字段类型错误。`--data-binary @文件` 发送原始 UTF-8 文件字节，并使 curl 使用 POST；`-i` 显示 HTTP 响应头。curl 的进程退出码不等于 HTTP 状态码，要看响应中的 200/422。

TODO 完成前，服务可以启动、`/docs` 可以展示接口、错误输入可以返回 422；调用未实现的正常路径会返回 500，服务器终端显示 NotImplementedError。完成后健康检查和正常分析不应再有 500 或 traceback。

验证结束在终端 A 按 Ctrl+C 停止服务。本日不需要生成结果文件。

## 完成标准

- Day 9 `10 passed`，Day 6～9 合计 `30 passed`，两项新增测试含上述真实断言。
- GET `/health` 返回 200/ok；POST 返回与 Day 6 相同的 schema_version、requirements、validation_errors 结构。
- 不同输入的分类结果正确；业务缺项返回 200 和具体错误；请求数据非法返回 422/detail。
- 通过真实 HTTP 验证正常/错误请求、响应头与日文内容，服务终端无正常路径 traceback；接口不写文件、不访问外部 API。
- 能用自己的话说明 JSON 解码、请求模型校验、业务校验三者的区别；学习后复盘与日语说明填写完成。
- 验收通过后更新进度，再按项目规则自动提交并推送 GitHub。脚手架就绪不代表当天已完成。

完成后告诉我：`Day 9 完成，请检查`。
