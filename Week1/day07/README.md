# Day 7 — HTTP JSON 客户端与错误边界

日期：2026-09-04（日本时间）

计划用时：90～120 分钟

唯一主主题：使用 `requests` 调用 JSON HTTP API，并用 Day 6 的 Pydantic Schema 校验响应。

## 今天要完成什么

实现下面这条最小链路：

```text
URL
  → requests.get(..., timeout=...)
  → 检查 HTTP 状态
  → 解析 JSON
  → RequirementData.model_validate(...)
  → 返回 RequirementData
```

外部 API 可能以五种方式返回结果：

1. HTTP 成功，JSON 结构正确：返回 `RequirementData`。
2. 连接失败或超时：抛出统一的 `RequirementApiError`。
3. HTTP 4xx/5xx：抛出统一的 `RequirementApiError`。
4. 响应不是合法 JSON：抛出统一的 `RequirementApiError`。
5. JSON 合法但不符合 Schema：抛出统一的 `RequirementApiError`。

今天不修改 Day 6 的 CLI 和解析器。Day 7 只练习“调用外部 API 的边界”，避免同时引入 FastAPI、异步和真实 LLM API。

## 今天只学这 7 个知识点

### 1. `requests.get()`

```python
response = requests.get(url, timeout=5.0)
```

它向 URL 发送 HTTP GET 请求，返回 `Response` 对象。`timeout` 必须显式设置，否则程序可能长时间等待。

### 2. `Response` 不是业务数据本身

可以先类比 Java：

```text
Response ≈ HTTP 客户端返回的响应对象
response.json() ≈ 把响应 body 反序列化成 Map / List
```

`response.json()` 返回普通 Python 数据，不会自动变成 `RequirementData`。

### 3. `raise_for_status()`

```python
response.raise_for_status()
```

HTTP 4xx/5xx 时抛出 `HTTPError`。必须先检查 HTTP 状态，再把 body 当作正常数据处理。JSON 能成功解析，不代表 HTTP 请求成功。

### 4. 用 Pydantic 检查 JSON 结构

```python
payload = response.json()
requirement = RequirementData.model_validate(payload)
```

第一行只解决“是不是合法 JSON”，第二行才检查字段名、字段类型和未知字段。

### 5. Requests 的异常父类

连接失败、超时、HTTP 错误和 Requests 的 JSON 解码错误，都属于 `requests.RequestException` 体系。当天只捕获这个父类，不分别处理重试策略。

### 6. 自定义异常与继承

```python
class RequirementApiError(RuntimeError):
    pass
```

括号中的 `RuntimeError` 是父类，相当于 Java 的：

```java
class RequirementApiError extends RuntimeException
```

这样调用方只需理解本项目的 `RequirementApiError`，不必知道底层究竟是超时、HTTP 错误还是 JSON 错误。

### 7. 返回类型标注

```python
def fetch_requirement(url: str) -> RequirementData:
```

- `url: str`：参数预期是字符串。
- `-> RequirementData`：正常返回值预期是 `RequirementData`。
- 它主要帮助 IDE、静态检查和阅读代码；Python 本身不会仅凭箭头自动验证返回值。

## Java 对照速查

| Python / Requests | Java 中可以先类比为 |
|---|---|
| `requests.get()` | HTTP client 的 GET 调用 |
| `Response` | HTTP response 对象 |
| `response.raise_for_status()` | 非 2xx 时主动抛异常 |
| `response.json()` | JSON body 转成 Map / List |
| `RequirementData.model_validate()` | Map 绑定并校验成 DTO |
| `class A(RuntimeError)` | `class A extends RuntimeException` |
| `-> RequirementData` | 方法声明的返回类型，但 Python 运行时不强制 |

今天不学习：`Session`、认证、Cookie、上传文件、代理、重试、流式响应、异步 HTTP、泛型、`Protocol` 或 mock 框架。

官方资料只作为扩展查阅：[Requests Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)。完成今天任务不需要通读。

## 需要完成的 6 个 TODO

| TODO | 文件 | 内容 |
|---|---|---|
| TODO 1 | `api_client.py` | 让 `RequirementApiError` 继承 `RuntimeError` |
| TODO 2 | `api_client.py` | 使用 `requests.get(url, timeout=timeout_seconds)` 获取响应 |
| TODO 3 | `api_client.py` | 检查状态、解析 JSON、Pydantic 校验，并统一转换异常 |
| TODO 4 | `test_day07.py` | 补完正常响应测试 |
| TODO 5 | `test_day07.py` | 补完超时测试 |
| TODO 6 | `test_day07.py` | 补完 Schema 错误测试 |

## 0～15 分钟：安装并确认 Requests

在仓库根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-dev.txt
.\.venv\Scripts\python.exe -c "import requests; print(requests.__version__)"
```

项目仍使用根目录 `.venv`，不要为 Day 7 新建解释器。

## 15～30 分钟：先看懂签名与继承

打开 `Week1/day07/api_client.py`：

```python
class RequirementApiError(Exception):
    pass


def fetch_requirement(
    url: str,
    timeout_seconds: float = 5.0,
) -> RequirementData:
```

完成 TODO 1：把父类由 `Exception` 改成 `RuntimeError`。

这里的箭头只描述正常返回路径：成功时返回 `RequirementData`；失败时函数不会返回，而是抛出 `RequirementApiError`。

## 30～65 分钟：实现 HTTP 请求与统一错误

完成 TODO 2 和 TODO 3，处理顺序必须是：

1. 在 `try` 中调用 `requests.get(url, timeout=timeout_seconds)`。
2. 对响应调用 `raise_for_status()`。
3. 调用 `json()` 得到普通 Python 数据。
4. 使用 `RequirementData.model_validate(...)` 得到并返回模型。
5. 捕获 `(requests.RequestException, ValidationError)`。
6. 抛出 `RequirementApiError`，并使用 `raise ... from exc` 保留原始异常原因。

输出：成功返回 `RequirementData`。

异常：上述网络、HTTP、JSON 或 Schema 错误统一表现为 `RequirementApiError`。

不要捕获宽泛的 `Exception`，否则代码错误也可能被伪装成 API 错误。

## 65～95 分钟：补完三个测试

打开 `Week1/day07/test_day07.py`：

- TODO 4：模拟成功响应，断言 URL、`timeout_seconds` 和返回模型内容。
- TODO 5：让假的 `requests.get()` 抛出 `requests.Timeout`，断言对外得到 `RequirementApiError`。
- TODO 6：让响应返回 `{"functions": "not-a-list"}`，断言 Schema 错误被转换为 `RequirementApiError`。

`monkeypatch` 只是在测试期间临时把真实 `requests.get` 换成假的函数，不会修改 Requests，也不会访问互联网。

运行：

```powershell
.\.venv\Scripts\python.exe -m pytest .\Week1\day06\test_day06.py .\Week1\day07\test_day07.py -q
```

初始脚手架预计为 `8 passed, 7 failed`；完成后应为 `15 passed`。

## 95～110 分钟：本地 HTTP 手动验收

测试通过后，可以用本机服务器验证一次真实 HTTP 请求，不访问外网。

终端 A（启动服务器）：

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory .\Week1\day07
```

终端 B（调用客户端）：

```powershell
.\.venv\Scripts\python.exe -c "from Week1.day07 import fetch_requirement; print(fetch_requirement('http://127.0.0.1:8000/sample_requirement.json'))"
```

成功后回到终端 A 按 `Ctrl+C` 停止服务器。

## 完成标准

- Day 6 与 Day 7 合计 `15 passed`。
- 成功时返回 `RequirementData`，并且请求使用调用者传入的 timeout。
- 超时、HTTP 4xx/5xx、非法 JSON、Schema 错误统一抛出 `RequirementApiError`。
- `RequirementApiError.__cause__` 保留底层原始异常。
- 本地 HTTP 手动调用可以读取 `sample_requirement.json`。
- 完成 `day07_notes.md` 的学习后复盘。

完成后告诉我：

```text
Day 7 完成，请检查
```
