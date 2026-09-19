# Day 19 — 模型调用失败时，程序应该返回什么

状态：2026-09-19 已完成；本日 20 项、全仓 193 项测试通过，三条必做模拟验收通过。可选真实调用超时，不影响本日完成；自报用时 1h+。以下保留原学习步骤，已经实现后不用重跑初始失败状态。Day18 的空白和未完成真实对比保留。

## 0. 开始顺序（5 分钟）

1. 在 [day19_notes.md](./day19_notes.md) 填开始时间。
2. 在原项目根目录打开 CMD/Cmder，先运行初始检查。下面命令也适用于 PowerShell：

```text
.\.venv\Scripts\python.exe -m pytest Week3/day19 -q
```

预期 **5 passed、15 failed，退出 1**。15 项失败来自两个未实现函数和一个自写测试占位，都是 NotImplementedError，属于正常脚手架状态。

3. 先读第 1～3 节生产调用链和最小知识，再做第 4 节 TODO；完成后按第 5 节测试与模拟运行，最后填复盘。

实现之后不用回退代码补跑初始失败。使用根 `.venv` 的 Python 3.11，不新建环境、不新增依赖。

## 1. 今天接着哪一步做（5 分钟）

昨天程序在 `gateway.complete(request)` 中等待，或遇到 503。今天先解决调用这一层：成功时接住 raw；失败时明确返回失败原因。今天的 `ok=True` **只表示 complete 正常返回了字符串**，不保证字符串是合法 JSON，更不保证需求提取准确。

先看 [prompt.py](./prompt.py) 和 [gemini_gateway.py](./gemini_gateway.py)，再看 [call_service.py](./call_service.py)：

```text
build_request(text) → ModelRequest
                         ↓
call_once(gateway, request)        ← 今天你实现
  → gateway.complete(request)     ← 助手提供：只发一次 HTTP 请求
       ├─ 正常返回 raw 字符串
       └─ 抛出超时、HTTP 状态或网络异常
  → 返回 CallResult               ← 今天你实现
                         ↓
run_call.py → 打印结果，设置退出码   ← 助手提供
```

`CallResult` 是 call_service.py 中已提供的 dataclass，类似一个 Java 数据对象。四个字段是：

| 字段 | 表示什么 |
|---|---|
| ok | 这一次 complete 是否正常返回 |
| raw | 正常返回的原始字符串；失败时为 None |
| error | 本程序规定的失败原因字符串；成功时为 None |
| status_code | 收到的 HTTP 错误状态码，如 503；没有 HTTP 错误响应时为 None |

后面的题目问“返回什么”时，指的是这个 CallResult 的字段，或 classify_status 返回的字符串，不引入其他称呼。

## 2. 为什么本日代码都在 day19（5 分钟）

按最新 AGENTS 规则，先复制必要代码到当天目录，再在副本上调整；不直接 import 历史实现。

| 当前文件 | 来源与调整 |
|---|---|
| prompt.py | 从 Day15 复制 ModelRequest、完整规则和 build_request；仅清理旧 TODO 注释 |
| cases.json | 从 Day16 复制 A/B/C 自制样例；本日入口只使用 C |
| gemini_gateway.py | 从 Day16 复制后改造；保留 complete(request) → str、模型名及三个请求字段，改用已安装的 HTTPX 直接调用同一个 Interactions API |
| test_gateway.py | 从 Day16 请求映射测试改编，增加超时传递、一次请求和返回文本检查 |
| call_service.py / test_day19_extra.py | 今天你需要完成的文件 |
| scenarios.py / run_call.py / 其余测试 | 助手提供，无需改写 |

这样在本日文件就能看完整调用链。没有改历史文件，也没有搬入虚拟环境、密钥或无关服务模块。

这次改用直接 HTTP 调用，是为了明确控制重试行为；不用你研究 SDK 内部。HTTPX 是项目已有依赖，用法和此前 requests 的“发请求 → raise_for_status”相近，但两套库的异常类不同，不能混用。

## 3. 今天需要的最小知识（15～20 分钟）

### 3.1 三种失败怎样来到你的函数

- **超时**：等待某个网络阶段超过配置时间，抛 `httpx.TimeoutException` 的子类，例如 ReadTimeout、ConnectTimeout；不一定收到了 HTTP 响应。
- **HTTP 状态错误**：服务返回 503 等状态；适配器调用 `response.raise_for_status()` 后抛 `httpx.HTTPStatusError`。在 `except ... as exc` 中用 `exc.response.status_code` 取整数状态码。
- **其他请求错误**：例如无法建立网络连接，会抛 `httpx.RequestError` 的子类。不能把所有失败都解释成 Key 错误。

与 Java 对照：try/except 类似 try/catch；先匹配到哪个 except，就进入哪个分支，不会接着执行下面的 except。

需要记住的继承关系：

```text
httpx.RequestError
  ├─ httpx.TimeoutException
  │    ├─ httpx.ReadTimeout
  │    └─ httpx.ConnectTimeout
  └─ 其他网络请求异常，例如 ConnectError

httpx.HTTPStatusError 是另一支，不属于 RequestError
```

因此先处理具体的 TimeoutException，再处理较宽的 RequestError。类似 Java 捕获子类异常应放在父类异常前面；Python 不一定提前阻止错误顺序，所以要用测试验证。

最小语法例子（不是今天的实现答案）：

```python
try:
    count = int("abc")
except ValueError:
    count = None
```

这个例子只是把已知的转换失败改成数据。今天你把已知调用失败改成 CallResult。其他编程错误仍应该抛出，不能一律伪装成网络错误。

### 3.2 超时与重试由助手配置

- 本日适配器没有重试循环，HTTPX 默认也不自动重试；一次 complete 只发送一次请求。
- 网络各阶段等待限制为 10 秒。读取超时指等待下一段数据的时间，不等于整个命令必定 10 秒结束。
- 可选 `--live` 入口另有约 30 秒总等待上限，超时后停止子进程，返回 overall_timeout；调用前立即提示。这个保护已由助手提供，不需要学习 subprocess。
- Ctrl+C 可以取消可选真实调用。取消客户端等待并不能保证服务端也停止处理，不要据此推断是否计费。
- 默认模拟不会真正睡 10 秒；它直接抛同一种异常，让测试立即验证你的处理逻辑。

### 3.3 已核对的官方资料：只读所列小段

今天用官方错误说明替代新的腾讯课程章节，不额外布置课程阅读报告。

1. [Gemini API 错误表](https://ai.google.dev/gemini-api/docs/api-errors)：只看 401、403、429、503 四行。429 可能涉及速率或额度；503 表示服务暂时不可用。
2. [HTTPX 异常](https://www.python-httpx.org/exceptions/)：只看异常继承树的 RequestError、TimeoutException、HTTPStatusError。
3. [HTTPX 超时](https://www.python-httpx.org/advanced/timeouts/)：只看 read timeout 的解释，理解“等下一段数据”和“总时长”的区别。

适配器参考 [Gemini REST 入门](https://ai.google.dev/gemini-api/docs/get-started#rest) 的请求及 steps/model_output 返回结构；[HTTPX transport](https://www.python-httpx.org/advanced/transports/) 用于助手的离线验证，无需学习整页。

今天不学：自动重试策略、指数退避、异步、线程/进程管理、SDK 内部实现、RAG、模型内容评分。旧日的 decode_requirements/evaluate 也不搬来重写，今天只检查调用是否完成。

## 4. 你要完成的三个 TODO（35～45 分钟）

读懂前面的生产调用链后，再打开 test_day19.py 看测试。FakeGateway 是本地替身：complete 会记录请求，然后返回指定字符串，或抛指定异常；不连接模型。类型注解不强制它继承 GeminiGateway，只需提供 complete 方法。

### TODO 1：classify_status(status_code) — call_service.py

输入：HTTP 错误响应的整数状态码。输出：下表的字符串；不打印，不发请求，不做额外类型校验。

| 输入 status_code | 预期返回字符串 |
|---|---|
| 401 或 403 | `auth_error` |
| 429 | `rate_limited` |
| 503 | `service_unavailable` |
| 其余 HTTP 错误状态码 | `api_error` |

这里将 401/403 合并为本程序的认证/权限错误提示，不表示两者原始含义完全相同。

### TODO 2：call_once(gateway, request) — call_service.py

输入：有 complete 方法的 gateway，以及 ModelRequest。先调用 `gateway.complete(request)`，**只调用一次**，然后按下表返回 CallResult：

| complete 的执行结果 | ok | raw | error | status_code |
|---|---|---|---|---|
| 正常返回字符串 | True | 原样保留字符串 | None | None |
| 抛 TimeoutException 或其子类 | False | None | `timeout` | None |
| 抛 HTTPStatusError | False | None | 用 classify_status 判断 | exc.response.status_code |
| 抛其他 RequestError 子类 | False | None | `network_error` | None |

处理要求：

1. 用 try/except 包住调用，具体超时放在 RequestError 前面。
2. 成功保留 raw，不在此处 loads、解析需求或打分。即使替身返回 `"not-json"`，本层仍返回 ok=True；内容检查属于后续步骤。
3. HTTPStatusError 分支提取状态码，并调用 TODO 1；失败时 raw 必须为 None，不能拿样例输出冒充成功。
4. 不把 `str(exc)`、密钥、请求头或错误响应正文放进返回结果；只用表中的固定字符串与状态码。
5. 不 sleep，不自动重试，不 print。未列出的异常，如 ValueError，应继续抛出；不要用 `except Exception` 把所有错误都吞掉。CLI 最外层的兜底由助手提供。

完成条件：14 项提供的业务测试通过，包括成功、HTTP 错误、超时、网络错误、原始字符串保留、一次调用和编程错误继续抛出。

### TODO 3：连接超时测试 — test_day19_extra.py

现有测试用了 ReadTimeout。你独立补充 ConnectTimeout，确认程序没有把它当成普通 network_error。

按顺序构造：

1. `request = build_request("CSV")`。
2. 用已导入的 FakeGateway，令 `error` 为 `httpx.ConnectTimeout("offline timeout")`。
3. 调用 `call_once(gateway, request)` 并接住返回值。
4. 断言完整返回值是 `CallResult(False, None, "timeout", None)`。
5. 再断言 `gateway.calls == [request]`，确认只调用一次。

这两项断言分别验证返回内容和调用次数。不要只执行函数、不检查结果。完成后本日应为 **20 passed**。

## 5. 实现后依次运行（15 分钟）

### 5.1 自动测试

```text
.\.venv\Scripts\python.exe -m pytest Week3/day19 -q
.\.venv\Scripts\python.exe -m pytest -q
```

当前完整学习工作区基准：本日 20 passed、全仓 193 passed。全仓数量随其他学习日是否已同步而变化；仅同步至 Day17 再加本日时为 182 项。本日应有 20 项通过，所有 pytest 测试都离线。

### 5.2 必做：本地模拟三条命令

```text
.\.venv\Scripts\python.exe -m Week3.day19.run_call --scenario success
.\.venv\Scripts\python.exe -m Week3.day19.run_call --scenario timeout
.\.venv\Scripts\python.exe -m Week3.day19.run_call --scenario unavailable
```

- success：ok=True，保留模拟 raw，error/status_code 为 None，退出 0。
- timeout：ok=False、raw=None、error="timeout"、status_code=None，退出 1。
- unavailable：ok=False、raw=None、error="service_unavailable"、status_code=503，退出 1。

后两条返回 1 是预期失败场景，正确处理它们就符合要求。输出 mode 必须是 simulated，不记成真实 Gemini 结果。还可选试 rate_limit、auth、network，不强制重复全部操作。

提示文字在 stderr，最终报告在 stdout，报告是一行 JSON，不生成结果文件。TODO 未实现、参数/配置错误或未预期异常退出 2。Python 的 None 在 JSON 中显示为 null，True/False 显示为 true/false。

### 5.3 可选：单次真实调用（不计入今日必做验收）

只有本地测试和模拟检查通过后，愿意尝试才运行：

```text
.\.venv\Scripts\python.exe -m Week3.day19.run_call --live
```

继续使用用户级环境变量中的 Key，不粘贴到命令里。只调用复制到本日的 C，一次请求；不会运行 Day18 的新旧对比。网络等待超过 10 秒返回 timeout，整个子进程超出约 30 秒返回 overall_timeout，均退出 1；缺少 Key 等配置问题退出 2；Ctrl+C 取消退出 130。

30 秒是子进程等待预算，启动与清理可能有少量额外耗时。接口恢复与否不影响本日作业完成；失败就如实记录，无需不断重跑。本日 adapter 只支持简单文本调用，未覆盖工具、多模态或全部异常响应结构。

## 6. 验收和复盘（10 分钟）

- 两个函数和自写测试完成，20 项本日测试及历史测试通过。
- 三条必做模拟命令的结果、退出码正确；错误结果不含异常正文或请求头，无自动重试。
- 能根据具体输入解释返回字段及异常处理顺序，按笔记题目回答即可。
- 填写自报用时和反馈，结束时间保持笔记最后一行。真实调用可留空，不把模拟结果当成模型效果。

### 助手脚手架验证（无需学习者另外执行）

- 2026-09-19：本日 5 passed、15 项 TODO 预期失败；全仓 178 passed、15 项预期失败，历史 173 项全部通过。
- HTTPX 本地模拟确认：请求字段和完整原文保留；503/读取超时均只发送一次；10 秒读取超时配置传入请求，返回值只取最终模型文本。
- 参考实现仅在验证进程中替换：19 项提供测试通过，另核对 ConnectTimeout 的完整返回值与一次调用；六种模拟 CLI 的 JSON、提示和退出码符合契约。参考答案未写入文件。
- 用本地休眠子进程和临时缩短的等待预算验证总超时分支，子进程被停止；未请求 Gemini。可选真实路径尚未以真实模型结果验证，不当作模型效果证据。
